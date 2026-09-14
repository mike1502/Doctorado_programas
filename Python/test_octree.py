# -*- coding: utf-8 -*-
"""
Created on Mon Sep 14 14:03:39 2026

@author: MCarrilloL

TEST OCTREE
"""

"""
Demostracion didactica: mallador octree tipo Hercules (CMU-Quake),
aplicado a un caso de juguete: 3 capas de suelo + un edificio de 2 niveles.

No es el codigo real de Hercules -- es una reimplementacion minima en
Python de las DOS reglas que gobiernan su mallador, para poder
visualizarlas:

  1) Criterio de resolucion por longitud de onda local:
         e(x) <= Vs_local(x) / (f_max * n_ppw)
     es decir, el tamano de arista del octante debe ser lo bastante
     chico para muestrear con "n_ppw" puntos por longitud de onda la
     frecuencia maxima f_max que se quiere resolver, usando la Vs del
     material que hay en el centroide de ese octante. Materiales mas
     blandos (Vs baja) -> octantes mas chicos automaticamente.

  2) Regla de balance 2:1 ("balanced octree"):
     dos octantes vecinos (que comparten cara) no pueden diferir en
     mas de un nivel de refinamiento. Donde esto se viola, el octante
     mas grande se subdivide, generando nodos "colgantes" en la cara
     compartida (que en un codigo FE real se restringen por
     interpolacion lineal a los nodos ancla del octante grande).

Simplificaciones deliberadas frente a Hercules real (se documentan
explicitamente, no son un descuido):
  - El dominio raiz aqui NO se rellena hasta un cubo perfecto; se usa
    directamente la caja rectangular del problema. Esto hace que los
    octantes mas profundos dejen de ser cubos perfectos (quedan con
    una relacion de aspecto fija). Hercules real rellena (pad) el
    dominio hasta un cubo para garantizar elementos cubicos exactos.
  - Los materiales se muestrean solo en el centroide de cada octante
    (igual que Hercules), lo que produce fronteras tipo "escalera"
    entre capas/edificio -- esto SI es fiel al comportamiento real.
  - El acoplamiento suelo-estructura aqui es la simplificacion mas
    fuerte: el edificio se trata como un material mas que ocupa el
    volumen por encima de la superficie libre (z=0) dentro de su
    huella en planta, en vez de una subestructuracion FE separada
    acoplada en la cimentacion (que es como se maneja SSI de forma
    mas rigurosa en la practica).
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 (necesario para proj3d)
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# ----------------------------------------------------------------------
# 1. Definicion del problema: dominio, capas de suelo y edificio
# ----------------------------------------------------------------------

# Dominio total (m). z=0 es la superficie libre; z<0 es subsuelo,
# z>0 es el edificio.
DOMAIN = dict(xmin=0.0, xmax=40.0, ymin=0.0, ymax=40.0, zmin=-24.0, zmax=7.0)

# Capas de suelo: cada una definida por su rango de profundidad y sus
# propiedades. Vs en m/s, densidad en kg/m3 (valores ilustrativos, no
# corresponden a ningun sitio real).
SOIL_LAYERS = [
    dict(name="Capa 1 (blanda)",   z_top=0.0,   z_bot=-4.0,  vs=120.0, rho=1400.0, color="#f6c453"),
    dict(name="Capa 2 (media)",    z_top=-4.0,  z_bot=-12.0, vs=350.0, rho=1800.0, color="#e07a5f"),
    dict(name="Capa 3 (firme)",    z_top=-12.0, z_bot=-24.0, vs=700.0, rho=2100.0, color="#8d6b94"),
]

# Edificio: huella en planta + altura total dividida en 2 niveles.
BUILDING = dict(
    name="Edificio (2 niveles)",
    xmin=15.0, xmax=25.0,
    ymin=15.0, ymax=25.0,
    zmin=0.0, zmax=7.0,           # 2 niveles de 3.5 m
    n_floors=2,
    vs=1200.0, rho=2400.0,        # concreto, valor equivalente ilustrativo
    color="#2a9d8f",
)

# Criterio de resolucion sismica
F_MAX = 10.0        # Hz, frecuencia maxima que se quiere resolver
N_PPW = 8            # puntos por longitud de onda minimos exigidos

# Criterio geometrico adicional para poder "ver" la forma del edificio
# (el criterio de Vs solo no basta: el concreto es rigido y permitiria
# octantes grandes, pero entonces el edificio quedaria representado por
# uno o dos cubos y se perderia la geometria de los 2 niveles).
MIN_CELLS_ACROSS_BUILDING = 3   # minimo de octantes a lo largo de cada
                                  # dimension caracteristica del edificio

MAX_LEVEL = 7        # profundidad maxima del arbol (limite de seguridad)
MIN_LEVEL = 1         # al menos un nivel de subdivision inicial


# ----------------------------------------------------------------------
# 2. Consulta de material por punto (equivalente a la "material query"
#    de Hercules: dado un punto (x,y,z), regresa Vs, rho, etc.)
# ----------------------------------------------------------------------

def query_material(x, y, z):
    """Devuelve un dict con las propiedades del material en (x,y,z),
    o None si el punto cae fuera de cualquier region definida
    (por ejemplo, "aire" fuera de la huella del edificio, z>0)."""

    inside_building_xy = (BUILDING["xmin"] <= x <= BUILDING["xmax"] and
                           BUILDING["ymin"] <= y <= BUILDING["ymax"])

    if z >= 0.0:
        if inside_building_xy and BUILDING["zmin"] <= z <= BUILDING["zmax"]:
            return BUILDING
        return None   # "aire": fuera de la huella del edificio, sin material

    for layer in SOIL_LAYERS:
        if layer["z_bot"] <= z < layer["z_top"]:
            return layer

    return None   # fuera del dominio de suelo definido


def required_edge_size(material):
    """Tamano de arista maximo permitido por el criterio de longitud
    de onda, para el material dado."""
    return material["vs"] / (F_MAX * N_PPW)


# ----------------------------------------------------------------------
# 3. Nodo del octree
# ----------------------------------------------------------------------

class OctNode:
    __slots__ = ("bounds", "level", "children", "material")

    def __init__(self, bounds, level):
        self.bounds = bounds          # (xmin,xmax,ymin,ymax,zmin,zmax)
        self.level = level
        self.children = []             # vacio si es hoja
        self.material = None

    @property
    def is_leaf(self):
        return len(self.children) == 0

    @property
    def centroid(self):
        xmin, xmax, ymin, ymax, zmin, zmax = self.bounds
        return (0.5 * (xmin + xmax), 0.5 * (ymin + ymax), 0.5 * (zmin + zmax))

    @property
    def edge_lengths(self):
        xmin, xmax, ymin, ymax, zmin, zmax = self.bounds
        return (xmax - xmin, ymax - ymin, zmax - zmin)

    def contains_point(self, x, y, z):
        xmin, xmax, ymin, ymax, zmin, zmax = self.bounds
        return (xmin <= x <= xmax) and (ymin <= y <= ymax) and (zmin <= z <= zmax)


def split_bounds(bounds):
    """Divide una caja en 8 octantes iguales."""
    xmin, xmax, ymin, ymax, zmin, zmax = bounds
    xmid, ymid, zmid = 0.5 * (xmin + xmax), 0.5 * (ymin + ymax), 0.5 * (zmin + zmax)
    return [
        (xmin, xmid, ymin, ymid, zmin, zmid),
        (xmid, xmax, ymin, ymid, zmin, zmid),
        (xmin, xmid, ymid, ymax, zmin, zmid),
        (xmid, xmax, ymid, ymax, zmin, zmid),
        (xmin, xmid, ymin, ymid, zmid, zmax),
        (xmid, xmax, ymin, ymid, zmid, zmax),
        (xmin, xmid, ymid, ymax, zmid, zmax),
        (xmid, xmax, ymid, ymax, zmid, zmax),
    ]


def intersects_building(bounds):
    xmin, xmax, ymin, ymax, zmin, zmax = bounds
    b = BUILDING
    return (xmin < b["xmax"] and xmax > b["xmin"] and
            ymin < b["ymax"] and ymax > b["ymin"] and
            zmin < b["zmax"] and zmax > b["zmin"])


def needs_refinement(node):
    if node.level >= MAX_LEVEL:
        return False
    if node.level < MIN_LEVEL:
        return True

    cx, cy, cz = node.centroid
    mat = query_material(cx, cy, cz)
    ex, ey, ez = node.edge_lengths

    # Criterio 1: longitud de onda local (si hay material definido)
    if mat is not None:
        e_req = required_edge_size(mat)
        if max(ex, ey, ez) > e_req:
            return True

    # Criterio 2: resolver la geometria del edificio aunque su Vs alta
    # permitiria octantes grandes
    if intersects_building(node.bounds):
        b = BUILDING
        building_dims = (b["xmax"] - b["xmin"],
                          b["ymax"] - b["ymin"],
                          b["zmax"] - b["zmin"])
        min_building_dim = min(building_dims)
        if max(ex, ey, ez) > min_building_dim / MIN_CELLS_ACROSS_BUILDING:
            return True

    return False


def build_tree(bounds, level=0):
    node = OctNode(bounds, level)
    if needs_refinement(node):
        node.children = [build_tree(cb, level + 1) for cb in split_bounds(bounds)]
    else:
        cx, cy, cz = node.centroid
        node.material = query_material(cx, cy, cz)
    return node


# ----------------------------------------------------------------------
# 4. Balance 2:1
# ----------------------------------------------------------------------

def collect_leaves(node, out):
    if node.is_leaf:
        out.append(node)
    else:
        for c in node.children:
            collect_leaves(c, out)
    return out


def find_leaf(root, x, y, z):
    node = root
    if not node.contains_point(x, y, z):
        return None
    while not node.is_leaf:
        found = None
        for c in node.children:
            if c.contains_point(x, y, z):
                found = c
                break
        if found is None:
            return node
        node = found
    return node


def split_leaf_in_place(node):
    """Convierte una hoja en nodo interno con 8 hijos (sin re-evaluar
    el criterio de refinamiento: es un split "forzado" por balance)."""
    node.children = []
    for cb in split_bounds(node.bounds):
        child = OctNode(cb, node.level + 1)
        cx, cy, cz = child.centroid
        child.material = query_material(cx, cy, cz)
        node.children.append(child)
    node.material = None


def balance_tree(root, max_iter=20):
    """Aplica la regla 2:1: si un octante vecino (que comparte cara) es
    mas de un nivel mas grande, se subdivide. Itera hasta converger."""
    eps = 1e-6
    for _ in range(max_iter):
        leaves = collect_leaves(root, [])
        changed = False
        for leaf in leaves:
            xmin, xmax, ymin, ymax, zmin, zmax = leaf.bounds
            cx, cy, cz = leaf.centroid
            # puntos justo afuera de cada una de las 6 caras
            face_points = [
                (xmin - eps, cy, cz), (xmax + eps, cy, cz),
                (cx, ymin - eps, cz), (cx, ymax + eps, cz),
                (cx, cy, zmin - eps), (cx, cy, zmax + eps),
            ]
            for (px, py, pz) in face_points:
                if not (DOMAIN["xmin"] <= px <= DOMAIN["xmax"] and
                        DOMAIN["ymin"] <= py <= DOMAIN["ymax"] and
                        DOMAIN["zmin"] <= pz <= DOMAIN["zmax"]):
                    continue
                neighbor = find_leaf(root, px, py, pz)
                if neighbor is None or neighbor is leaf:
                    continue
                if neighbor.level < leaf.level - 1:
                    split_leaf_in_place(neighbor)
                    changed = True
        if not changed:
            break
    return root


# ----------------------------------------------------------------------
# 5. Construccion del arbol
# ----------------------------------------------------------------------

def build_octree():
    root_bounds = (DOMAIN["xmin"], DOMAIN["xmax"],
                    DOMAIN["ymin"], DOMAIN["ymax"],
                    DOMAIN["zmin"], DOMAIN["zmax"])
    root = build_tree(root_bounds, level=0)
    balance_tree(root)
    return root


def material_color(material):
    if material is None:
        return "white"
    return material["color"]


# ----------------------------------------------------------------------
# 6. Visualizacion
# ----------------------------------------------------------------------

def plot_cross_section(root, y_slice, ax, title):
    """Corte vertical x-z en y = y_slice: dibuja los octantes que
    intersectan ese plano, coloreados por material."""
    leaves = collect_leaves(root, [])
    for leaf in leaves:
        xmin, xmax, ymin, ymax, zmin, zmax = leaf.bounds
        if not (ymin <= y_slice <= ymax):
            continue
        color = material_color(leaf.material)
        rect = Rectangle((xmin, zmin), xmax - xmin, zmax - zmin,
                          facecolor=color, edgecolor="black", linewidth=0.4,
                          alpha=0.9 if leaf.material is not None else 0.05)
        ax.add_patch(rect)
    ax.set_xlim(DOMAIN["xmin"], DOMAIN["xmax"])
    ax.set_ylim(DOMAIN["zmin"], DOMAIN["zmax"])
    ax.axhline(0.0, color="black", linewidth=1.0, linestyle="--")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("z (m)  [z=0: superficie libre]")
    ax.set_title(title)
    ax.set_aspect("equal")


def plot_3d_octants(root, ax, max_leaves_to_draw=4000):
    """Vista 3D de los octantes (subconjunto si el arbol es grande, para
    no saturar la figura)."""
    leaves = collect_leaves(root, [])
    if len(leaves) > max_leaves_to_draw:
        rng = np.random.default_rng(0)
        idx = rng.choice(len(leaves), size=max_leaves_to_draw, replace=False)
        leaves = [leaves[i] for i in idx]

    for leaf in leaves:
        if leaf.material is None:
            continue  # no dibujar "aire" para no saturar la vista 3D
        xmin, xmax, ymin, ymax, zmin, zmax = leaf.bounds
        color = material_color(leaf.material)
        verts = cube_faces(xmin, xmax, ymin, ymax, zmin, zmax)
        poly = Poly3DCollection(verts, facecolor=color, edgecolor="k",
                                 linewidths=0.2, alpha=0.55)
        ax.add_collection3d(poly)

    ax.set_xlim(DOMAIN["xmin"], DOMAIN["xmax"])
    ax.set_ylim(DOMAIN["ymin"], DOMAIN["ymax"])
    ax.set_zlim(DOMAIN["zmin"], DOMAIN["zmax"])
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_zlabel("z (m)")
    ax.set_title("Vista 3D del octree (edificio + 3 capas de suelo)")
    try:
        ax.set_box_aspect((DOMAIN["xmax"] - DOMAIN["xmin"],
                            DOMAIN["ymax"] - DOMAIN["ymin"],
                            DOMAIN["zmax"] - DOMAIN["zmin"]))
    except AttributeError:
        pass  # versiones viejas de matplotlib no tienen set_box_aspect


def cube_faces(xmin, xmax, ymin, ymax, zmin, zmax):
    pts = {
        "000": (xmin, ymin, zmin), "100": (xmax, ymin, zmin),
        "110": (xmax, ymax, zmin), "010": (xmin, ymax, zmin),
        "001": (xmin, ymin, zmax), "101": (xmax, ymin, zmax),
        "111": (xmax, ymax, zmax), "011": (xmin, ymax, zmax),
    }
    faces = [
        [pts["000"], pts["100"], pts["110"], pts["010"]],   # z=zmin
        [pts["001"], pts["101"], pts["111"], pts["011"]],   # z=zmax
        [pts["000"], pts["100"], pts["101"], pts["001"]],   # y=ymin
        [pts["010"], pts["110"], pts["111"], pts["011"]],   # y=ymax
        [pts["000"], pts["010"], pts["011"], pts["001"]],   # x=xmin
        [pts["100"], pts["110"], pts["111"], pts["101"]],   # x=xmax
    ]
    return faces


# ----------------------------------------------------------------------
# 7. Programa principal
# ----------------------------------------------------------------------

def main():
    root = build_octree()
    leaves = collect_leaves(root, [])

    print(f"Numero total de octantes (hojas): {len(leaves)}")
    sizes = [max(l.edge_lengths) for l in leaves]
    print(f"Tamano de arista maximo (octante mas grueso): {max(sizes):.2f} m")
    print(f"Tamano de arista minimo (octante mas fino):   {min(sizes):.2f} m")

    by_material = {}
    for l in leaves:
        name = l.material["name"] if l.material is not None else "exterior/aire"
        by_material[name] = by_material.get(name, 0) + 1
    print("\nOctantes por material:")
    for name, count in by_material.items():
        print(f"  {name:20s}: {count}")

    y_building_center = 0.5 * (BUILDING["ymin"] + BUILDING["ymax"])

    fig = plt.figure(figsize=(13, 6.2))

    ax1 = fig.add_subplot(1, 2, 1)
    plot_cross_section(root, y_building_center, ax1,
                        f"Corte vertical (y = {y_building_center:.0f} m,\n"
                        f"pasa por el centro del edificio)")

    ax2 = fig.add_subplot(1, 2, 2, projection="3d")
    plot_3d_octants(root, ax2)

    fig.suptitle(
        "Mallador octree tipo Hercules -- caso sencillo:\n"
        "edificio de 2 niveles sobre 3 capas de suelo",
        fontsize=12,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(r"C:\Users\MCarrilloL\Documents\GitHub\Doctorado_programas\Python\octree_demo_result.png", dpi=170)
    print("\nFigura guardada en: octree_demo_result.png")


if __name__ == "__main__":
    main()
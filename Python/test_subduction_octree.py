"""
Demostracion didactica: mallador octree tipo Hercules aplicado a un
CORTE ILUSTRATIVO de una zona de subduccion (placa oceanica subduciendo
bajo placa continental).

Extiende la logica del demo anterior (edificio + 3 capas) con dos
elementos nuevos que vale la pena resaltar:

  1) La interfaz de placas NO es horizontal: es una superficie curva
     e inclinada (aqui, un perfil simplificado de dos tramos: somero
     cerca de la trinchera, mas inclinado en profundidad -- un "kink"
     tipico de los esquemas didacticos de subduccion). Esto obliga a
     una regla de refinamiento nueva que no usamos en el demo anterior:

  2) Criterio de deteccion de interfaz: se muestrean las esquinas de
     cada octante; si caen en materiales distintos, el octante se seguira
     subdividiendo (hasta un tamano minimo objetivo cerca de la interfaz)
     independientemente de si el criterio de longitud de onda ya se
     habia cumplido. Esto es lo que produce una malla fina "pegada" a
     la interfaz curva de placas, en vez de solo fronteras horizontales
     tipo escalera como en el demo de capas planas.

  3) Vista "cutaway": para poder ver la placa subducida completa en
     perspectiva, se oculta el bloque superior (corteza continental +
     cuna del manto) solo en la mitad del dominio a lo largo del rumbo
     (direccion y), dejando la placa oceanica subducida visible en todo
     el dominio. Es puramente un truco de visualizacion, no afecta la
     malla en si (la malla se calcula igual en todo el dominio).

Igual que el demo anterior: esto NO es el codigo real de Hercules, es
una reimplementacion minima en Python de sus reglas de mallado, con
fines ilustrativos. Las unidades aqui son kilometros (escala regional),
no metros.
"""

import os
import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# ----------------------------------------------------------------------
# 1. Dominio y geometria de la interfaz de placas
# ----------------------------------------------------------------------

# Dominio (km). x: distancia horizontal desde la trinchera (0 = trinchera).
# y: direccion a lo largo del rumbo de la fosa. z: profundidad (z=0 es
# la superficie libre, z<0 es hacia el interior de la Tierra).
DOMAIN = dict(xmin=0.0, xmax=300.0, ymin=0.0, ymax=150.0, zmin=-150.0, zmax=0.0)

# Perfil de la interfaz de placas: dos tramos rectos con distinto echado
# (aproximacion tipo "kink", habitual en esquemas didacticos de
# subduccion). dip en grados.
SLAB_KINK_X = 100.0      # km desde la trinchera donde cambia el echado
SLAB_DIP_SHALLOW = 12.0  # grados, tramo somero (cerca de la trinchera)
SLAB_DIP_STEEP = 45.0    # grados, tramo profundo

SLAB_CRUST_THICKNESS = 7.0     # km, espesor de la corteza oceanica subducida
SLAB_MANTLE_THICKNESS = 45.0   # km, espesor del manto litosferico oceanico
CONTINENTAL_CRUST_THICKNESS = 35.0  # km, espesor de la corteza continental


def slab_top_depth(x):
    """Profundidad (negativa, km) de la parte superior de la placa
    subducida, en funcion de la distancia x a la trinchera."""
    if x <= 0:
        return 0.0
    d1 = SLAB_KINK_X * math.tan(math.radians(SLAB_DIP_SHALLOW))
    if x <= SLAB_KINK_X:
        depth = x * math.tan(math.radians(SLAB_DIP_SHALLOW))
    else:
        depth = d1 + (x - SLAB_KINK_X) * math.tan(math.radians(SLAB_DIP_STEEP))
    return -depth


# ----------------------------------------------------------------------
# 2. Materiales (propiedades ilustrativas, no de un sitio real)
# ----------------------------------------------------------------------

CONTINENTAL_CRUST = dict(name="Corteza continental", vs=3.5, color="#d9a066")
MANTLE_WEDGE      = dict(name="Cuna del manto",       vs=4.4, color="#e63946")
SLAB_CRUST        = dict(name="Corteza oceanica (placa subducida)", vs=3.8, color="#1d3557")
SLAB_MANTLE       = dict(name="Manto litosferico oceanico",         vs=4.6, color="#457b9d")
SUB_SLAB_MANTLE   = dict(name="Manto (astenosfera)",  vs=4.5, color="#adb5bd")

# Materiales que forman el "bloque de arriba" (los que se ocultaran a
# la mitad para la vista en corte / cutaway)
OVERRIDING_BLOCK_NAMES = {CONTINENTAL_CRUST["name"], MANTLE_WEDGE["name"]}


def query_material(x, y, z):
    if z > DOMAIN["zmax"] + 1e-9:
        return None  # por arriba de la superficie libre

    z_top = slab_top_depth(x)
    z_crust_bot = z_top - SLAB_CRUST_THICKNESS
    z_mantle_bot = z_crust_bot - SLAB_MANTLE_THICKNESS

    if z >= z_top:
        crust_bot = max(-CONTINENTAL_CRUST_THICKNESS, z_top)
        if z >= crust_bot:
            return CONTINENTAL_CRUST
        else:
            return MANTLE_WEDGE
    elif z >= z_crust_bot:
        return SLAB_CRUST
    elif z >= z_mantle_bot:
        return SLAB_MANTLE
    else:
        return SUB_SLAB_MANTLE


# ----------------------------------------------------------------------
# 3. Criterio de resolucion
# ----------------------------------------------------------------------

F_MAX = 0.03          # Hz -- escala regional (periodos largos, ~30 s)
N_PPW = 8              # puntos por longitud de onda

INTERFACE_TARGET_SIZE = 6.0   # km, tamano objetivo de octante cerca de
                                # cualquier interfaz entre materiales
MAX_LEVEL = 7
MIN_LEVEL = 2


def required_edge_size(material):
    return material["vs"] / (F_MAX * N_PPW)


# ----------------------------------------------------------------------
# 4. Nodo del octree (identico en estructura al demo anterior)
# ----------------------------------------------------------------------

class OctNode:
    __slots__ = ("bounds", "level", "children", "material")

    def __init__(self, bounds, level):
        self.bounds = bounds
        self.level = level
        self.children = []
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


def corner_materials(bounds):
    """Material en cada una de las 8 esquinas del octante (para detectar
    si el octante esta a caballo sobre una interfaz)."""
    xmin, xmax, ymin, ymax, zmin, zmax = bounds
    ymid = 0.5 * (ymin + ymax)  # el material no depende de y: basta 1 valor
    names = set()
    for xx in (xmin, xmax):
        for zz in (zmin, zmax):
            m = query_material(xx, ymid, zz)
            names.add(m["name"] if m is not None else None)
    return names


def needs_refinement(node):
    if node.level >= MAX_LEVEL:
        return False
    if node.level < MIN_LEVEL:
        return True

    ex, ey, ez = node.edge_lengths
    names = corner_materials(node.bounds)

    if len(names) > 1:
        # el octante cruza una interfaz entre materiales: refinar hasta
        # el tamano objetivo de interfaz, sin importar el criterio de
        # longitud de onda
        return max(ex, ez) > INTERFACE_TARGET_SIZE

    # octante homogeneo: criterio de longitud de onda del material local
    cx, cy, cz = node.centroid
    mat = query_material(cx, cy, cz)
    if mat is None:
        return False
    e_req = required_edge_size(mat)
    return max(ex, ez) > e_req


def build_tree(bounds, level=0):
    node = OctNode(bounds, level)
    if needs_refinement(node):
        node.children = [build_tree(cb, level + 1) for cb in split_bounds(bounds)]
    else:
        cx, cy, cz = node.centroid
        node.material = query_material(cx, cy, cz)
    return node


# ----------------------------------------------------------------------
# 5. Balance 2:1 (identico al demo anterior)
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
    node.children = []
    for cb in split_bounds(node.bounds):
        child = OctNode(cb, node.level + 1)
        cx, cy, cz = child.centroid
        child.material = query_material(cx, cy, cz)
        node.children.append(child)
    node.material = None


def balance_tree(root, max_iter=25):
    eps = 1e-6
    for _ in range(max_iter):
        leaves = collect_leaves(root, [])
        changed = False
        for leaf in leaves:
            xmin, xmax, ymin, ymax, zmin, zmax = leaf.bounds
            cx, cy, cz = leaf.centroid
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


def build_octree():
    root_bounds = (DOMAIN["xmin"], DOMAIN["xmax"],
                    DOMAIN["ymin"], DOMAIN["ymax"],
                    DOMAIN["zmin"], DOMAIN["zmax"])
    root = build_tree(root_bounds, level=0)
    balance_tree(root)
    return root


def material_color(material):
    return "white" if material is None else material["color"]


# ----------------------------------------------------------------------
# 6. Visualizacion
# ----------------------------------------------------------------------

def cube_faces(xmin, xmax, ymin, ymax, zmin, zmax):
    pts = {
        "000": (xmin, ymin, zmin), "100": (xmax, ymin, zmin),
        "110": (xmax, ymax, zmin), "010": (xmin, ymax, zmin),
        "001": (xmin, ymin, zmax), "101": (xmax, ymin, zmax),
        "111": (xmax, ymax, zmax), "011": (xmin, ymax, zmax),
    }
    return [
        [pts["000"], pts["100"], pts["110"], pts["010"]],
        [pts["001"], pts["101"], pts["111"], pts["011"]],
        [pts["000"], pts["100"], pts["101"], pts["001"]],
        [pts["010"], pts["110"], pts["111"], pts["011"]],
        [pts["000"], pts["010"], pts["011"], pts["001"]],
        [pts["100"], pts["110"], pts["111"], pts["101"]],
    ]


def plot_cross_section(root, y_slice, ax):
    leaves = collect_leaves(root, [])
    for leaf in leaves:
        xmin, xmax, ymin, ymax, zmin, zmax = leaf.bounds
        if not (ymin <= y_slice <= ymax):
            continue
        color = material_color(leaf.material)
        rect = Rectangle((xmin, zmin), xmax - xmin, zmax - zmin,
                          facecolor=color, edgecolor="black", linewidth=0.25)
        ax.add_patch(rect)

    # curva de la interfaz de placas, para resaltarla
    xs = np.linspace(DOMAIN["xmin"], DOMAIN["xmax"], 300)
    zs = [slab_top_depth(x) for x in xs]
    ax.plot(xs, zs, color="yellow", linewidth=1.8, linestyle="--",
             label="Interfaz de placas")

    ax.set_xlim(DOMAIN["xmin"], DOMAIN["xmax"])
    ax.set_ylim(DOMAIN["zmin"], DOMAIN["zmax"])
    ax.set_xlabel("x: distancia desde la trinchera (km)")
    ax.set_ylabel("z: profundidad (km)")
    ax.set_title(f"Corte vertical completo (y = {y_slice:.0f} km)")
    ax.set_aspect("equal")
    ax.legend(loc="lower right", fontsize=8)


def is_visible_leaf(leaf, root, cutaway_y):
    """Un octante es 'visible' (debe dibujarse) si al menos una de sus
    6 caras esta expuesta: toca el borde del dominio, toca la region
    oculta por el corte (cutaway), o es vecina de un material distinto.
    Los octantes totalmente rodeados de material identico (interior
    solido, invisible de todas formas) se omiten -- esto evita dibujar
    decenas de miles de caras que no se ven y elimina el artefacto de
    'huecos' que deja el submuestreo aleatorio."""
    xmin, xmax, ymin, ymax, zmin, zmax = leaf.bounds
    cx, cy, cz = leaf.centroid
    eps = 1e-6
    leaf_name = leaf.material["name"] if leaf.material is not None else None

    face_centers = [
        (xmin - eps, cy, cz), (xmax + eps, cy, cz),
        (cx, ymin - eps, cz), (cx, ymax + eps, cz),
        (cx, cy, zmin - eps), (cx, cy, zmax + eps),
    ]
    for (px, py, pz) in face_centers:
        if not (DOMAIN["xmin"] <= px <= DOMAIN["xmax"] and
                DOMAIN["ymin"] <= py <= DOMAIN["ymax"] and
                DOMAIN["zmin"] <= pz <= DOMAIN["zmax"]):
            return True  # toca el borde exterior del dominio

        neighbor = find_leaf(root, px, py, pz)
        if neighbor is None:
            return True

        neighbor_name = neighbor.material["name"] if neighbor.material is not None else None
        neighbor_hidden = (neighbor_name in OVERRIDING_BLOCK_NAMES and
                            0.5 * (neighbor.bounds[2] + neighbor.bounds[3]) < cutaway_y)
        if neighbor_hidden:
            return True  # cara expuesta por el corte (cutaway)
        if neighbor_name != leaf_name:
            return True  # frontera entre materiales distintos

    return False  # completamente rodeado de material identico: no se ve


def plot_3d_cutaway(root, ax, cutaway_y):
    """Vista 3D en perspectiva: el bloque superior (corteza continental +
    cuna del manto) se dibuja solo para y <= cutaway_y; la placa
    subducida y el manto inferior se dibujan en todo el dominio. Solo
    se dibujan los octantes con al menos una cara visible (ver
    is_visible_leaf), no toda la malla."""
    leaves = collect_leaves(root, [])

    active = []
    for leaf in leaves:
        if leaf.material is None:
            continue
        y_center = 0.5 * (leaf.bounds[2] + leaf.bounds[3])
        if leaf.material["name"] in OVERRIDING_BLOCK_NAMES and y_center < cutaway_y:
            continue  # oculto por el corte (se deja el bloque superior al fondo)
        active.append(leaf)

    to_draw = [leaf for leaf in active if is_visible_leaf(leaf, root, cutaway_y)]
    print(f"Octantes activos (no ocultos por el corte): {len(active)}")
    print(f"Octantes efectivamente dibujados (superficie visible): {len(to_draw)}")

    for leaf in to_draw:
        xmin, xmax, ymin, ymax, zmin, zmax = leaf.bounds
        color = material_color(leaf.material)
        verts = cube_faces(xmin, xmax, ymin, ymax, zmin, zmax)
        poly = Poly3DCollection(verts, facecolor=color, edgecolor="k",
                                 linewidths=0.15, alpha=0.97)
        ax.add_collection3d(poly)

    ax.set_xlim(DOMAIN["xmin"], DOMAIN["xmax"])
    ax.set_ylim(DOMAIN["ymin"], DOMAIN["ymax"])
    ax.set_zlim(DOMAIN["zmin"], DOMAIN["zmax"])
    ax.set_xlabel("x: distancia a la trinchera (km)")
    ax.set_ylabel("y: rumbo (km)")
    ax.set_zlabel("z: profundidad (km)")
    ax.set_title("Vista 3D con corte (cutaway) del bloque superior")
    ax.view_init(elev=18, azim=-55)

    # Etiquetas de referencia para verificar la orientacion (frente/fondo)
    ax.text(DOMAIN["xmin"], DOMAIN["ymin"], 8, "y=0", fontsize=9, color="black")
    ax.text(DOMAIN["xmin"], DOMAIN["ymax"], 8, "y=150", fontsize=9, color="black")
    try:
        ax.set_box_aspect((DOMAIN["xmax"] - DOMAIN["xmin"],
                            DOMAIN["ymax"] - DOMAIN["ymin"],
                            (DOMAIN["zmax"] - DOMAIN["zmin"])))
    except AttributeError:
        pass


def build_legend_handles():
    from matplotlib.patches import Patch
    materials = [CONTINENTAL_CRUST, MANTLE_WEDGE, SLAB_CRUST, SLAB_MANTLE, SUB_SLAB_MANTLE]
    return [Patch(facecolor=m["color"], edgecolor="black", label=m["name"]) for m in materials]


# ----------------------------------------------------------------------
# 7. Programa principal
# ----------------------------------------------------------------------

def main():
    root = build_octree()
    leaves = collect_leaves(root, [])

    print(f"Numero total de octantes (hojas): {len(leaves)}")
    sizes = [max(l.edge_lengths[0], l.edge_lengths[2]) for l in leaves]
    print(f"Tamano de arista (x,z) maximo: {max(sizes):.2f} km")
    print(f"Tamano de arista (x,z) minimo: {min(sizes):.2f} km")

    by_material = {}
    for l in leaves:
        name = l.material["name"] if l.material is not None else "fuera de dominio"
        by_material[name] = by_material.get(name, 0) + 1
    print("\nOctantes por material:")
    for name, count in by_material.items():
        print(f"  {name:38s}: {count}")

    y_mid = 0.5 * (DOMAIN["ymin"] + DOMAIN["ymax"])

    fig = plt.figure(figsize=(14, 6.5))

    ax1 = fig.add_subplot(1, 2, 1)
    plot_cross_section(root, y_mid, ax1)

    ax2 = fig.add_subplot(1, 2, 2, projection="3d")
    plot_3d_cutaway(root, ax2, cutaway_y=y_mid)

    handles = build_legend_handles()
    fig.legend(handles=handles, loc="lower center", ncol=5, fontsize=8,
                bbox_to_anchor=(0.5, -0.02))

    fig.suptitle(
        "Mallador octree tipo Hercules -- corte ilustrativo de zona de subduccion",
        fontsize=13,
    )
    fig.tight_layout(rect=[0, 0.04, 1, 0.94])

    OUTPUT_DIR = "."   # <-- cambia por tu carpeta de destino si quieres
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, "octree_subduction_result.png")
    fig.savefig(output_path, dpi=170)
    print(f"\nFigura guardada en: {output_path}")


if __name__ == "__main__":
    main()
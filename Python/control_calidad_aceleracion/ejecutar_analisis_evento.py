"""
ejecutar_analisis_evento.py
Programa principal de ejecución optimizado para SPYDER y terminal.

INSTRUCCIONES PARA USAR EN SPYDER:
1. Abre este archivo (ejecutar_analisis_evento.py) en Spyder.
2. Modifica la sección de "CONFIGURACIÓN USER / SPYDER" más abajo según necesites:
   - Para analizar UN SOLO EVENTO: Cambia la ruta en 'CARPETA_EVENTO_A_PROCESAR' y deja PROCESAR_TODA_LA_BASE_DE_DATOS = False.
   - Para analizar TODAS LAS CARPETAS (72): Cambia PROCESAR_TODA_LA_BASE_DE_DATOS = True.
3. Presiona F5 (o el botón verde de "Run/Play") en Spyder.
"""

import os
import sys

# Asegurar importación de módulos locales
dir_script = os.path.dirname(os.path.abspath(__file__))
if dir_script not in sys.path:
    sys.path.insert(0, dir_script)

from estadisticas_base_datos import analizar_carpeta_evento, analizar_toda_base_datos
from graficar_mapa_mixcoac import generar_mapa_estatico, generar_mapa_interactivo
from graficar_formas_onda import graficar_sismogramas_estacion, graficar_parrilla_estaciones


# ==============================================================================
#                 ⚙️ CONFIGURACIÓN PARA SPYDER (EDITA AQUÍ)
# ==============================================================================

# ¿Deseas analizar toda la base de datos de 72 carpetas de un solo golpe?
#   False -> Analiza solo la carpeta especificada en 'CARPETA_EVENTO_A_PROCESAR'
#   True  -> Analiza automáticamente TODAS las carpetas dentro de 'CARPETA_BASE_DATOS_GENERAL'
PROCESAR_TODA_LA_BASE_DE_DATOS = True


# 1. Ruta de la carpeta del evento específico que deseas analizar (para modo individual):
CARPETA_EVENTO_A_PROCESAR = r"C:\Users\MCarrilloL\Documents\Doctorado\FallaFinita_Registros\base_datos\2023_12_03_0029_02_M2_CDMX\ACEL\ASA"


# 2. Ruta raíz donde están contenidas todas las carpetas de eventos:
CARPETA_BASE_DATOS_GENERAL = r"C:\Users\MCarrilloL\Documents\Doctorado\FallaFinita_Registros\base_datos"

# ==============================================================================


def procesar_un_evento(dir_asa):
    """Procesa una sola carpeta de evento y genera mapas, CSV, Excel y gráficos."""
    print("=" * 80)
    print("      ANÁLISIS Y CONTROL DE CALIDAD DE ACELEROGRAMAS (EVENTO INDIVIDUAL)")
    print("=" * 80)
    print(f"Ruta procesada: {dir_asa}\n")

    if not os.path.exists(dir_asa):
        print(f"ERROR: La carpeta especificada no existe:\n   {dir_asa}")
        return

    # Determinar nombre del evento a partir de la ruta
    partes = dir_asa.replace('/', '\\').split('\\')
    nombre_evento = "evento"
    for i, p in enumerate(partes):
        if p.upper() in ['ACEL', 'ASA', 'ASA2.0'] and i > 0:
            nombre_evento = partes[i-1]
            break
    if nombre_evento == "evento":
        nombre_evento = os.path.basename(dir_asa)

    dir_salida_evento = os.path.join(dir_script, f"resultados_{nombre_evento}")
    dir_salida_sismogramas = os.path.join(dir_salida_evento, "sismogramas_estaciones")
    os.makedirs(dir_salida_sismogramas, exist_ok=True)

    # 1. Extracción de Metadatos y Estadísticas
    print("[1/4] Extrayendo metadatos y calculando estadísticas...")
    df_meta, stats, datos_eventos = analizar_carpeta_evento(dir_asa, dir_salida=dir_salida_evento)

    print("\n--- RESUMEN ESTADÍSTICO DEL EVENTO ---")
    print(f"• Evento:                 {stats['carpeta_evento']}")
    print(f"• Fecha / Hora (GMT):     {stats['fecha_sismo']} {stats['hora_sismo']}")
    print(f"• Magnitud:               {stats['magnitud']}")
    print(f"• Epicentro (Lat, Lon):   {stats['epicentro_lat']} N, {stats['epicentro_lon']} W")
    print(f"• Profundidad Focal:      {stats['profundidad_km']} km")
    print(f"• Total Registros ASA:    {stats['total_registros']}")
    print(f"• Registros Válidos:      {stats['registros_validos']}")
    print(f"• Registros con Falla:    {stats['registros_con_falla']}")
    print(f"• PGA Máximo Global:      {stats['pga_maximo_evento_gal']:.4f} Gal (Estación: {stats['estacion_pga_maximo']})")
    print(f"• Rango de Distancia:     {stats['distancia_epicentral_min_km']} km - {stats['distancia_epicentral_max_km']} km")
    print(f"• Sensores Utilizados:   {', '.join(stats['modelos_sensores'])}")
    print(f"• Tipos de Suelo:        {', '.join(stats['tipos_suelo_presentes'])}\n")

    # 2. Generación de Mapas (Zona Mixcoac / CDMX)
    print("[2/4] Generando mapas (estático PNG e interactivo HTML Plotly)...")
    png_mapa = os.path.join(dir_salida_evento, "mapa_pga_mixcoac_estatico.png")
    html_mapa = os.path.join(dir_salida_evento, "mapa_pga_mixcoac_interactivo.html")

    generar_mapa_estatico(df_meta, output_png=png_mapa, titulo=f"PGA Máximo - Evento {nombre_evento}")
    generar_mapa_interactivo(df_meta, output_html=html_mapa, titulo=f"Mapa Interactivo PGA - Evento {nombre_evento}")

    # 3. Control de Calidad de Formas de Onda Multi-Estación
    print("[3/4] Generando parrilla de control de calidad para las estaciones principales...")
    png_parrilla = os.path.join(dir_salida_evento, "parrilla_qc_multi_estacion.png")
    graficar_parrilla_estaciones(datos_eventos, output_png=png_parrilla, max_estaciones=9, aplicar_filtro=False)

    # 4. Graficación Individual por Estación
    print("[4/4] Generando sismogramas individuales de 3 componentes por estación...")
    for st_code, st_data in datos_eventos.items():
        out_st_png = os.path.join(dir_salida_sismogramas, f"waveforms_{st_code}.png")
        graficar_sismogramas_estacion(
            st_data['meta'],
            st_data['times'],
            st_data['channels'],
            output_png=out_st_png,
            aplicar_filtro=False
        )

    print("\n" + "=" * 80)
    print("   [OK] ANÁLISIS DEL EVENTO COMPLETADO EXITOSAMENTE")
    print("=" * 80)
    print(f"Resultados guardados en: {dir_salida_evento}")
    print(f"  - Detalle Metadatos CSV:     {os.path.join(dir_salida_evento, 'metadatos_evento_detalle.csv')}")
    print(f"  - Detalle Metadatos Excel:   {os.path.join(dir_salida_evento, 'metadatos_evento_detalle.xlsx')}")
    print(f"  - Mapa Estático PNG:         {png_mapa}")
    print(f"  - Mapa Interactivo HTML:     {html_mapa}")
    print(f"  - Parrilla QC PNG:           {png_parrilla}")
    print(f"  - Sismogramas en:            {dir_salida_sismogramas}")
    print("=" * 80 + "\n")


def procesar_toda_la_base(dir_base):
    """Escanea y procesa todas las subcarpetas de eventos dentro de la base de datos."""
    print("=" * 80)
    print("   PROCESANDO TODAS LAS CARPETAS (72) DE LA BASE DE DATOS")
    print("=" * 80)
    dir_salida_global = os.path.join(dir_script, "resultados_globales_base_datos")
    analizar_toda_base_datos(dir_base, dir_salida=dir_salida_global)
    print("\n" + "=" * 80)
    print("   [OK] BASE DE DATOS PROCESADA COMPLETAMENTE")
    print("=" * 80)
    print(f"Archivos Excel/CSV globales generados en: {dir_salida_global}\n")


if __name__ == "__main__":
    if PROCESAR_TODA_LA_BASE_DE_DATOS:
        procesar_toda_la_base(CARPETA_BASE_DATOS_GENERAL)
    else:
        procesar_un_evento(CARPETA_EVENTO_A_PROCESAR)

"""
estadisticas_base_datos.py
Módulo para la extracción masiva de metadatos, análisis estadístico y control de calidad
tanto por carpeta de evento sismológico como para toda la base de datos de acelerogramas.
"""

import os
import glob
import pandas as pd
import numpy as np
from asa_parser import parse_asa_file


def analizar_carpeta_evento(dir_asa, dir_salida=None):
    """
    Analiza todos los archivos ASA dentro de la carpeta de un evento específico.
    Retorna un DataFrame con todos los metadatos y un diccionario con las estadísticas del evento.
    """
    if not os.path.exists(dir_asa):
        raise FileNotFoundError(f"La carpeta especificada no existe: {dir_asa}")

    archivos = glob.glob(os.path.join(dir_asa, "*"))
    archivos = [f for f in archivos if os.path.isfile(f) and not f.endswith('.py') and not f.endswith('.txt') and not f.endswith('.csv') and not f.endswith('.xlsx')]

    registros_meta = []
    datos_eventos_dict = {}

    for filepath in archivos:
        meta, times, channels = parse_asa_file(filepath)
        registros_meta.append(meta)
        if meta['calidad_status'] == 'OK' and channels is not None:
            datos_eventos_dict[meta['estacion_clave']] = {
                'meta': meta,
                'times': times,
                'channels': channels
            }

    df_event = pd.DataFrame(registros_meta)

    # Calcular Estadísticas Resumen del Evento
    total_archivos = len(df_event)
    validos = len(df_event[df_event['calidad_status'] == 'OK'])
    con_fallas = total_archivos - validos

    pga_max_global = df_event['pga_max_gal'].max() if 'pga_max_gal' in df_event and not df_event['pga_max_gal'].isnull().all() else 0.0
    estacion_pga_max = df_event.loc[df_event['pga_max_gal'].idxmax()]['estacion_clave'] if validos > 0 else 'N/A'

    dist_min = df_event['distancia_epicentral_km'].min() if 'distancia_epicentral_km' in df_event else None
    dist_max = df_event['distancia_epicentral_km'].max() if 'distancia_epicentral_km' in df_event else None

    sismo_fecha = df_event['sismo_fecha'].iloc[0] if not df_event.empty and 'sismo_fecha' in df_event else 'Desconocida'
    sismo_hora = df_event['sismo_hora'].iloc[0] if not df_event.empty and 'sismo_hora' in df_event else 'Desconocida'
    sismo_mag = df_event['sismo_mag'].iloc[0] if not df_event.empty and 'sismo_mag' in df_event else 'Desconocida'
    sismo_lat = df_event['sismo_lat'].iloc[0] if not df_event.empty and 'sismo_lat' in df_event else None
    sismo_lon = df_event['sismo_lon'].iloc[0] if not df_event.empty and 'sismo_lon' in df_event else None
    sismo_prof = df_event['sismo_prof_km'].iloc[0] if not df_event.empty and 'sismo_prof_km' in df_event else None

    sensores_unicos = df_event['sensor_modelo'].unique().tolist() if 'sensor_modelo' in df_event else []
    tipos_suelo = df_event['tipo_suelo'].unique().tolist() if 'tipo_suelo' in df_event else []

    estadisticas = {
        'carpeta_evento': os.path.basename(os.path.dirname(os.path.dirname(dir_asa))),
        'fecha_sismo': sismo_fecha,
        'hora_sismo': sismo_hora,
        'magnitud': sismo_mag,
        'epicentro_lat': sismo_lat,
        'epicentro_lon': sismo_lon,
        'profundidad_km': sismo_prof,
        'total_registros': total_archivos,
        'registros_validos': validos,
        'registros_con_falla': con_fallas,
        'pga_maximo_evento_gal': pga_max_global,
        'estacion_pga_maximo': estacion_pga_max,
        'distancia_epicentral_min_km': dist_min,
        'distancia_epicentral_max_km': dist_max,
        'modelos_sensores': [s for s in sensores_unicos if s],
        'tipos_suelo_presentes': [t for t in tipos_suelo if t]
    }

    # Exportar resultados si se especificó carpeta de salida
    if dir_salida:
        os.makedirs(dir_salida, exist_ok=True)
        csv_path = os.path.join(dir_salida, "metadatos_evento_detalle.csv")
        excel_path = os.path.join(dir_salida, "metadatos_evento_detalle.xlsx")
        
        # Eliminar columnas no serializables en CSV/Excel si las hubiera
        df_export = df_event.copy()
        if 'orientaciones' in df_export.columns:
            df_export['orientaciones'] = df_export['orientaciones'].apply(lambda x: "/".join(x) if isinstance(x, list) else str(x))
        if 'calidad_observaciones' in df_export.columns:
            df_export['calidad_observaciones'] = df_export['calidad_observaciones'].apply(lambda x: "; ".join(x) if isinstance(x, list) else str(x))
            
        df_export.to_csv(csv_path, index=False, encoding='utf-8-sig')
        try:
            df_export.to_excel(excel_path, index=False)
        except Exception:
            pass

    return df_event, estadisticas, datos_eventos_dict


def analizar_toda_base_datos(dir_base_datos, dir_salida=None):
    """
    Escanea recursivamente la carpeta base de datos buscando todas las subcarpetas de eventos ACEL/ASA.
    Genera un reporte estadístico consolidado de toda la base de datos.
    """
    if not os.path.exists(dir_base_datos):
        raise FileNotFoundError(f"La ruta de la base de datos no existe: {dir_base_datos}")

    carpetas_asa = glob.glob(os.path.join(dir_base_datos, "**", "ACEL", "ASA"), recursive=True)
    print(f"Total de carpetas de eventos ASA encontradas en la base de datos: {len(carpetas_asa)}")

    todos_los_registros = []
    resumen_eventos = []

    for idx, carpeta in enumerate(sorted(carpetas_asa), 1):
        try:
            df_event, stats, _ = analizar_carpeta_evento(carpeta)
            todos_los_registros.append(df_event)
            resumen_eventos.append(stats)
            print(f"[{idx}/{len(carpetas_asa)}] Procesado: {stats['carpeta_evento']} - {stats['registros_validos']} registros válidos.")
        except Exception as e:
            print(f"[{idx}/{len(carpetas_asa)}] Error procesando carpeta {carpeta}: {e}")

    df_global_registros = pd.concat(todos_los_registros, ignore_index=True) if todos_los_registros else pd.DataFrame()
    df_global_eventos = pd.DataFrame(resumen_eventos)

    if dir_salida:
        os.makedirs(dir_salida, exist_ok=True)
        csv_reg = os.path.join(dir_salida, "base_datos_global_registros.csv")
        excel_reg = os.path.join(dir_salida, "base_datos_global_registros.xlsx")
        csv_eve = os.path.join(dir_salida, "base_datos_global_resumen_eventos.csv")
        excel_eve = os.path.join(dir_salida, "base_datos_global_resumen_eventos.xlsx")

        if not df_global_registros.empty:
            df_reg_exp = df_global_registros.copy()
            if 'orientaciones' in df_reg_exp.columns:
                df_reg_exp['orientaciones'] = df_reg_exp['orientaciones'].apply(lambda x: "/".join(x) if isinstance(x, list) else str(x))
            if 'calidad_observaciones' in df_reg_exp.columns:
                df_reg_exp['calidad_observaciones'] = df_reg_exp['calidad_observaciones'].apply(lambda x: "; ".join(x) if isinstance(x, list) else str(x))
            df_reg_exp.to_csv(csv_reg, index=False, encoding='utf-8-sig')
            try: df_reg_exp.to_excel(excel_reg, index=False)
            except: pass

        if not df_global_eventos.empty:
            df_eve_exp = df_global_eventos.copy()
            for col in ['modelos_sensores', 'tipos_suelo_presentes']:
                if col in df_eve_exp.columns:
                    df_eve_exp[col] = df_eve_exp[col].apply(lambda x: "/".join(x) if isinstance(x, list) else str(x))
            df_eve_exp.to_csv(csv_eve, index=False, encoding='utf-8-sig')
            try: df_eve_exp.to_excel(excel_eve, index=False)
            except: pass

    return df_global_registros, df_global_eventos

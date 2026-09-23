"""
asa_parser.py
Módulo para la lectura y procesamiento de archivos estándar de aceleración (formato ASA v2.0 - UNAM).
Extrae metadatos de la estación, acelerógrafo, sismo, registro, calcula PGA, distancia epicentral,
azimut y verifica la calidad del registro.
"""

import os
import re
import math
import numpy as np
import pandas as pd


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calcula la distancia ortodrómica en km entre dos puntos (WGS84)."""
    if None in (lat1, lon1, lat2, lon2):
        return None
    R = 6371.0  # Radio medio de la Tierra en km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def calculate_azimuth(lat1, lon1, lat2, lon2):
    """Calcula el azimut (grados desde el Norte) del punto 1 al punto 2."""
    if None in (lat1, lon1, lat2, lon2):
        return None
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - \
        math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    az = math.degrees(math.atan2(y, x))
    return (az + 360.0) % 360.0


def classify_channel(chan_name):
    """Mapea nombres de canales (HLZ, HNE, +V, N00E, etc.) a Z, N, E."""
    c = str(chan_name).upper()
    if 'Z' in c or '+V' in c or '-V' in c:
        return 'Z'
    elif 'N' in c and 'W' not in c and 'E' not in c:
        return 'N'
    elif '00' in c:
        return 'N'
    elif 'E' in c or 'W' in c or '90' in c:
        return 'E'
    return 'Z'


def parse_asa_file(filepath):
    """
    Parsea un archivo ASA individual.
    Retorna un diccionario completo con metadatos, series de tiempo y banderas de calidad.
    """
    filename = os.path.basename(filepath)
    st_code = filename[:4]
    
    meta = {
        'archivo': filename,
        'ruta_completa': filepath,
        'estacion_clave': st_code,
        'estacion_nombre': '',
        'localizacion': '',
        'estacion_lat': None,
        'estacion_lon': None,
        'estacion_altitud_msnm': None,
        'tipo_suelo': '',
        'institucion': '',
        'sensor_modelo': '',
        'sensor_serie': '',
        'num_canales': 3,
        'orientaciones': [],
        'fs_hz': 100.0,
        'dt_s': 0.01,
        'sismo_fecha': '',
        'sismo_hora': '',
        'sismo_mag': '',
        'sismo_lat': None,
        'sismo_lon': None,
        'sismo_prof_km': None,
        'sismo_fuente': '',
        'registro_hora_inicio': '',
        'duraciones_s': [],
        'num_muestras_reportadas': [],
        'pga_reportado_gal': [],
        'unidades': 'Gal',
        'origen_seisan': '',
        'distancia_epicentral_km': None,
        'azimut_deg': None,
        'pga_z_gal': None,
        'pga_n_gal': None,
        'pga_e_gal': None,
        'pga_max_gal': None,
        'calidad_status': 'OK',
        'calidad_observaciones': []
    }

    try:
        with open(filepath, 'r', encoding='latin1', errors='replace') as f:
            lines = f.readlines()
    except Exception as e:
        meta['calidad_status'] = 'ERROR_LECTURA'
        meta['calidad_observaciones'].append(f"No se pudo abrir el archivo: {e}")
        return meta, None, None

    in_data = False
    data_lines = []

    def extract_val(line_str):
        if ':' in line_str:
            return line_str.split(':', 1)[1].strip()
        return ''

    for i, line in enumerate(lines):
        line_clean = line.strip()

        # Parsear Secciones del Header
        if 'NOMBRE DE LA ESTACION' in line:
            meta['estacion_nombre'] = extract_val(line)
        elif 'CLAVE DE LA ESTACION' in line:
            val = extract_val(line)
            if val: meta['estacion_clave'] = val
        elif 'LOCALIZACION DE LA ESTACION' in line:
            meta['localizacion'] = extract_val(line)
        elif 'COORDENADAS DE LA ESTACION' in line:
            sub1 = extract_val(line)
            sub2 = extract_val(lines[i+1]) if i+1 < len(lines) else ''
            for txt in [sub1, sub2]:
                if 'LAT' in txt:
                    m = re.search(r'([0-9]+\.?[0-9]*)', txt)
                    if m: meta['estacion_lat'] = float(m.group(1))
                elif 'LONG' in txt:
                    m = re.search(r'([0-9]+\.?[0-9]*)', txt)
                    if m: meta['estacion_lon'] = -float(m.group(1))
        elif 'ALTITUD (msnm)' in line:
            val = extract_val(line)
            if val:
                try: meta['estacion_altitud_msnm'] = float(val)
                except: pass
        elif 'TIPO DE SUELO' in line:
            meta['tipo_suelo'] = extract_val(line)
        elif 'INSTITUCION RESPONSABLE' in line:
            meta['institucion'] = extract_val(line)
        elif 'MODELO DEL ACELEROGRAFO' in line:
            meta['sensor_modelo'] = extract_val(line)
        elif 'NUMERO DE SERIE DEL ACELEROGRAFO' in line:
            meta['sensor_serie'] = extract_val(line)
        elif 'ORIENTACION C1-C6' in line:
            raw = extract_val(line)
            meta['orientaciones'] = [p.strip() for p in raw.split('/') if p.strip()]
        elif 'VEL. DE MUESTREO, C1-C6' in line:
            raw = extract_val(line)
            parts = [p.strip() for p in raw.split('/') if p.strip()]
            if parts:
                try:
                    meta['fs_hz'] = float(parts[0])
                    meta['dt_s'] = 1.0 / meta['fs_hz'] if meta['fs_hz'] > 0 else 0.01
                except: pass
        elif 'FECHA DEL SISMO' in line:
            meta['sismo_fecha'] = extract_val(line)
        elif 'HORA EPICENTRO' in line:
            meta['sismo_hora'] = extract_val(line)
        elif 'MAGNITUD(ES)' in line:
            meta['sismo_mag'] = extract_val(line)
        elif 'COORDENADAS DEL EPICENTRO' in line:
            sub1 = extract_val(line)
            sub2 = extract_val(lines[i+1]) if i+1 < len(lines) else ''
            for txt in [sub1, sub2]:
                if 'LAT' in txt:
                    m = re.search(r'([0-9]+\.?[0-9]*)', txt)
                    if m: meta['sismo_lat'] = float(m.group(1))
                elif 'LONG' in txt:
                    m = re.search(r'([0-9]+\.?[0-9]*)', txt)
                    if m: meta['sismo_lon'] = -float(m.group(1))
        elif 'PROFUNDIDAD FOCAL' in line:
            val = extract_val(line)
            if val:
                try: meta['sismo_prof_km'] = float(val)
                except: pass
        elif 'HORA DE LA PRIMERA MUESTRA' in line:
            meta['registro_hora_inicio'] = extract_val(line)
        elif 'DURACION DEL REGISTRO (s)' in line:
            raw = extract_val(line)
            meta['duraciones_s'] = [float(p) for p in raw.split('/') if p.strip() and re.match(r'^-?\d+(\.\d+)?$', p.strip())]
        elif 'ACEL. MAX.(Gal)' in line:
            raw = extract_val(line)
            meta['pga_reportado_gal'] = [float(p) for p in raw.split('/') if p.strip() and re.match(r'^-?\d+(\.\d+)?$', p.strip())]
        elif 'Archivo de origen en formato SEISAN:' in line:
            meta['origen_seisan'] = extract_val(line)
        elif 'DATOS DE ACELERACION:' in line:
            in_data = True
            continue

        if in_data:
            if '---------' in line_clean or 'CANAL' in line_clean:
                continue
            parts = line_clean.split()
            if len(parts) >= 3:
                try:
                    vals = [float(p) for p in parts[:3]]
                    data_lines.append(vals)
                except:
                    pass

    data_arr = np.array(data_lines)
    if data_arr.size == 0:
        meta['calidad_status'] = 'SIN_DATOS'
        meta['calidad_observaciones'].append("El archivo no contiene matrices de datos de aceleración válidas.")
        return meta, None, None

    # Mapeo de canales y cálculo de series de tiempo
    npts, num_cols = data_arr.shape
    times = np.arange(npts) * meta['dt_s']

    mapped_chans = [classify_channel(c) for c in meta['orientaciones']] if meta['orientaciones'] else ['Z', 'N', 'E']
    channels_dict = {}

    for idx in range(min(num_cols, len(mapped_chans))):
        comp = mapped_chans[idx]
        channels_dict[comp] = data_arr[:, idx]

    # Calcular PGA directo desde los datos
    pga_vals = np.max(np.abs(data_arr), axis=0)
    if len(pga_vals) >= 1: meta['pga_z_gal'] = float(pga_vals[0])
    if len(pga_vals) >= 2: meta['pga_n_gal'] = float(pga_vals[1])
    if len(pga_vals) >= 3: meta['pga_e_gal'] = float(pga_vals[2])
    meta['pga_max_gal'] = float(np.max(pga_vals))

    # Calcular Distancia Epicentral y Azimut
    if meta['estacion_lat'] and meta['estacion_lon'] and meta['sismo_lat'] and meta['sismo_lon']:
        meta['distancia_epicentral_km'] = round(haversine_distance(
            meta['sismo_lat'], meta['sismo_lon'], meta['estacion_lat'], meta['estacion_lon']), 3)
        meta['azimut_deg'] = round(calculate_azimuth(
            meta['sismo_lat'], meta['sismo_lon'], meta['estacion_lat'], meta['estacion_lon']), 2)
    else:
        meta['calidad_observaciones'].append("Coordenadas incompletas para cálculo de distancia/azimut.")

    # Verificaciones adicionales de calidad
    if meta['pga_max_gal'] < 1e-4:
        meta['calidad_status'] = 'SENAL_CERO'
        meta['calidad_observaciones'].append("Amplitud máxima nula o extremadamente cercana a cero.")
    elif npts < 100:
        meta['calidad_status'] = 'INCOMPLETO'
        meta['calidad_observaciones'].append("Registro muy corto (menos de 100 muestras).")

    return meta, times, channels_dict

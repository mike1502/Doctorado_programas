"""
graficar_mapa_mixcoac.py
Módulo para la visualización cartográfica en Python de la red de acelerógrafos en la zona de Mixcoac / CDMX.
Genera mapas estáticos de alta resolución (Matplotlib) y mapas interactivos independientes (Plotly HTML).
"""

import os
import matplotlib
matplotlib.use('Agg')  # Usar backend no interactivo para salvar imágenes sin conflicto de GUI
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import plotly.graph_objects as go
import pandas as pd
import numpy as np


def generar_mapa_estatico(df_meta, output_png=None, titulo="Mapa de Aceleración Máxima (PGA) - Mixcoac / CDMX"):
    """
    Genera un mapa estático usando Matplotlib enfocado en la zona de Mixcoac / CDMX.
    """
    df_valid = df_meta.dropna(subset=['estacion_lat', 'estacion_lon']).copy()
    if df_valid.empty:
        print("No hay coordenadas válidas para generar el mapa estático.")
        return

    fig, ax = plt.subplots(figsize=(10, 8), dpi=300)

    # Extraer sismo epicenter info
    epi_lat = df_valid['sismo_lat'].iloc[0] if 'sismo_lat' in df_valid and not df_valid['sismo_lat'].isnull().all() else 19.37
    epi_lon = df_valid['sismo_lon'].iloc[0] if 'sismo_lon' in df_valid and not df_valid['sismo_lon'].isnull().all() else -99.22
    sismo_mag = df_valid['sismo_mag'].iloc[0] if 'sismo_mag' in df_valid else 'M2.0'

    # Normalizar valores de PGA para colorear
    pgas = df_valid['pga_max_gal'].fillna(0.0).values
    norm = mcolors.Normalize(vmin=max(0.0, float(np.min(pgas))), vmax=max(0.1, float(np.max(pgas))))
    cmap = cm.YlOrRd

    # Graficar estaciones
    sc = ax.scatter(
        df_valid['estacion_lon'],
        df_valid['estacion_lat'],
        c=pgas,
        cmap=cmap,
        norm=norm,
        s=120,
        edgecolors='black',
        linewidths=1.2,
        zorder=3,
        label='Estaciones Acelerográficas'
    )

    # Etiquetar cada estación con su clave y valor de PGA
    for _, row in df_valid.iterrows():
        st_txt = f"{row['estacion_clave']}\n({row['pga_max_gal']:.2f} Gal)" if pd.notnull(row['pga_max_gal']) else row['estacion_clave']
        ax.annotate(
            st_txt,
            (row['estacion_lon'], row['estacion_lat']),
            xytext=(5, 5),
            textcoords='offset points',
            fontsize=7,
            fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.7, edgecolor='none'),
            zorder=4
        )

    # Graficar Epicentro
    if epi_lat and epi_lon:
        ax.scatter(
            [epi_lon], [epi_lat],
            color='cyan',
            marker='*',
            s=350,
            edgecolors='black',
            linewidths=1.5,
            zorder=5,
            label=f'Epicentro ({sismo_mag})'
        )

    # Añadir barra de color
    cbar = fig.colorbar(sc, ax=ax, shrink=0.85, pad=0.02)
    cbar.set_label('PGA Máximo (Gal - cm/s²)', fontsize=10, fontweight='bold')

    # Configuración de ejes y retícula
    ax.set_xlabel('Longitud (°W)', fontsize=10, fontweight='bold')
    ax.set_ylabel('Latitud (°N)', fontsize=10, fontweight='bold')
    ax.set_title(titulo, fontsize=12, fontweight='bold', pad=15)
    ax.grid(True, linestyle='--', alpha=0.5, zorder=1)

    # Margen geográfico alrededor de los datos
    min_lon, max_lon = df_valid['estacion_lon'].min(), df_valid['estacion_lon'].max()
    min_lat, max_lat = df_valid['estacion_lat'].min(), df_valid['estacion_lat'].max()
    padding = 0.025
    ax.set_xlim(min_lon - padding, max_lon + padding)
    ax.set_ylim(min_lat - padding, max_lat + padding)

    ax.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.9)
    plt.tight_layout()

    if output_png:
        out_abs = os.path.abspath(output_png)
        os.makedirs(os.path.dirname(out_abs), exist_ok=True)
        fig.savefig(out_abs, dpi=300, bbox_inches='tight')
        print(f"Mapa estático guardado en: {out_abs}")
    plt.close(fig)


def generar_mapa_interactivo(df_meta, output_html=None, titulo="Mapa Interactivo - Red Acelerográfica Mixcoac / CDMX"):
    """
    Genera un mapa interactivo exportable en HTML usando Plotly.
    """
    df_valid = df_meta.dropna(subset=['estacion_lat', 'estacion_lon']).copy()
    if df_valid.empty:
        print("No hay coordenadas válidas para generar el mapa interactivo.")
        return

    epi_lat = df_valid['sismo_lat'].iloc[0] if 'sismo_lat' in df_valid and not df_valid['sismo_lat'].isnull().all() else 19.37
    epi_lon = df_valid['sismo_lon'].iloc[0] if 'sismo_lon' in df_valid and not df_valid['sismo_lon'].isnull().all() else -99.22
    sismo_mag = df_valid['sismo_mag'].iloc[0] if 'sismo_mag' in df_valid else 'M2.0'
    sismo_fecha = df_valid['sismo_fecha'].iloc[0] if 'sismo_fecha' in df_valid else ''
    sismo_hora = df_valid['sismo_hora'].iloc[0] if 'sismo_hora' in df_valid else ''

    # Texto Hover para Estaciones
    hover_texts = []
    for _, row in df_valid.iterrows():
        ht = (
            f"<b>Estación:</b> {row['estacion_clave']} ({row['estacion_nombre']})<br>"
            f"<b>Coordenadas:</b> {row['estacion_lat']:.5f} N, {row['estacion_lon']:.5f} W<br>"
            f"<b>Altitud:</b> {row['estacion_altitud_msnm']} msnm<br>"
            f"<b>Tipo de Suelo:</b> {row['tipo_suelo']}<br>"
            f"<b>Sensor:</b> {row['sensor_modelo']} (S/N: {row['sensor_serie']})<br>"
            f"<b>Distancia Epicentral:</b> {row['distancia_epicentral_km']} km<br>"
            f"<b>Azimut:</b> {row['azimut_deg']}°<br>"
            f"<b>PGA Z:</b> {row['pga_z_gal']:.4f} Gal<br>"
            f"<b>PGA N:</b> {row['pga_n_gal']:.4f} Gal<br>"
            f"<b>PGA E:</b> {row['pga_e_gal']:.4f} Gal<br>"
            f"<b>PGA Máximo:</b> <b>{row['pga_max_gal']:.4f} Gal</b><br>"
            f"<b>Calidad:</b> {row['calidad_status']}"
        )
        hover_texts.append(ht)

    fig = go.Figure()

    # Trazar Estaciones
    fig.add_trace(go.Scattermapbox(
        lat=df_valid['estacion_lat'],
        lon=df_valid['estacion_lon'],
        mode='markers+text',
        marker=dict(
            size=14,
            color=df_valid['pga_max_gal'],
            colorscale='YlOrRd',
            showscale=True,
            colorbar=dict(title="PGA Max (Gal)"),
            cmin=0,
            cmax=df_valid['pga_max_gal'].max() if not df_valid['pga_max_gal'].empty else 1.0
        ),
        text=df_valid['estacion_clave'],
        textposition="top center",
        hoverinfo='text',
        hovertext=hover_texts,
        name='Estaciones ASA'
    ))

    # Trazar Epicentro
    if epi_lat and epi_lon:
        epi_hover = (
            f"<b>EPICENTRO SISMO</b><br>"
            f"Fecha: {sismo_fecha} {sismo_hora}<br>"
            f"Magnitud: {sismo_mag}<br>"
            f"Latitud: {epi_lat} N<br>"
            f"Longitud: {epi_lon} W"
        )
        fig.add_trace(go.Scattermapbox(
            lat=[epi_lat],
            lon=[epi_lon],
            mode='markers',
            marker=dict(
                size=22,
                color='red',
                symbol='star'
            ),
            hoverinfo='text',
            hovertext=[epi_hover],
            name=f'Epicentro ({sismo_mag})'
        ))

    # Centro de la vista del mapa
    center_lat = float(df_valid['estacion_lat'].mean())
    center_lon = float(df_valid['estacion_lon'].mean())

    fig.update_layout(
        title=dict(text=titulo, font=dict(size=16, color='#2c3e50')),
        mapbox=dict(
            style='open-street-map',
            center=dict(lat=center_lat, lon=center_lon),
            zoom=12
        ),
        margin=dict(l=20, r=20, t=50, b=20),
        height=750
    )

    if output_html:
        out_abs = os.path.abspath(output_html)
        os.makedirs(os.path.dirname(out_abs), exist_ok=True)
        fig.write_html(out_abs)
        print(f"Mapa interactivo guardado en: {out_abs}")

    return fig

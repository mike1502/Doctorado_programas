"""
graficar_formas_onda.py
Módulo para la graficación y control de calidad (QC) de formas de onda de aceleración (3 componentes).
Soporta procesamiento de señal opcional (demean, detrend, filtro pasa-banda Butterworth).
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal


def aplicar_filtro_pasabanda(data, fs, freqmin=0.1, freqmax=10.0):
    """Aplica filtro pasa-banda Butterworth usando SciPy."""
    if len(data) == 0 or fs <= 0:
        return data
    nyq = 0.5 * fs
    low = freqmin / nyq
    high = min(freqmax / nyq, 0.99)
    if low >= high or low <= 0:
        return data
    b, a = signal.butter(2, [low, high], btype='band')
    return signal.filtfilt(b, a, data)


def graficar_sismogramas_estacion(meta, times, channels, output_png=None, aplicar_filtro=False):
    """
    Grafica las 3 componentes (Z, N, E) de aceleración para una estación individual.
    """
    if channels is None or len(channels) == 0:
        return

    st_code = meta['estacion_clave']
    st_name = meta['estacion_nombre']
    dist = meta.get('distancia_epicentral_km', 'N/A')
    pga_max = meta.get('pga_max_gal', 0.0)

    fig, axes = plt.subplots(3, 1, figsize=(11, 7), sharex=True, dpi=200)
    fig.suptitle(
        f"Estación: {st_code} ({st_name}) | Distancia Epicentral: {dist} km | PGA Máx: {pga_max:.2f} Gal",
        fontsize=12, fontweight='bold', y=0.96
    )

    comps = ['Z', 'N', 'E']
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

    for i, comp in enumerate(comps):
        ax = axes[i]
        sig_raw = channels.get(comp)

        if sig_raw is not None and len(sig_raw) > 0:
            # Baseline correction
            sig_proc = signal.detrend(sig_raw - np.mean(sig_raw))
            if aplicar_filtro:
                sig_proc = aplicar_filtro_pasabanda(sig_proc, meta['fs_hz'], 0.1, 10.0)

            pga_comp = np.max(np.abs(sig_proc))
            ax.plot(times[:len(sig_proc)], sig_proc, color=colors[i], linewidth=0.8, label=f"Componente {comp}")
            ax.set_ylabel(f"Acel ({meta['unidades']})", fontsize=9, fontweight='bold')
            ax.grid(True, linestyle=':', alpha=0.6)
            ax.legend(loc='upper right', frameon=True, fontsize=8)

            # Texto descriptivo por componente
            ax.text(
                0.01, 0.85, f"PGA {comp}: {pga_comp:.4f} {meta['unidades']}",
                transform=ax.transAxes, fontsize=9, fontweight='bold',
                bbox=dict(boxstyle='square,pad=0.2', facecolor='white', alpha=0.8, edgecolor='gray')
            )
        else:
            ax.text(0.5, 0.5, f"Sin datos para componente {comp}", ha='center', va='center', transform=ax.transAxes)

    axes[-1].set_xlabel("Tiempo (s)", fontsize=10, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.94])

    if output_png:
        out_abs = os.path.abspath(output_png)
        os.makedirs(os.path.dirname(out_abs), exist_ok=True)
        fig.savefig(out_abs, bbox_inches='tight')
    plt.close(fig)


def graficar_parrilla_estaciones(datos_eventos_dict, output_png=None, max_estaciones=9, aplicar_filtro=False):
    """
    Grafica una parrilla multi-estación mostrando la componente de mayor amplitud o Vertical Z
    para control rápido de calidad del evento.
    """
    estaciones_validas = [st for st, data in datos_eventos_dict.items() if data['channels']]
    if not estaciones_validas:
        print("No hay estaciones válidas para la parrilla de control de calidad.")
        return

    # Ordenar estaciones por distancia epicentral o PGA
    estaciones_validas = sorted(
        estaciones_validas,
        key=lambda st: datos_eventos_dict[st]['meta'].get('pga_max_gal', 0.0),
        reverse=True
    )[:max_estaciones]

    n_est = len(estaciones_validas)
    n_cols = 3
    n_rows = int(np.ceil(n_est / n_cols))

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 3 * n_rows), dpi=200, sharex=True)
    fig.suptitle(f"Control de Calidad Multi-Estación (PGA Máximo) - {n_est} Estaciones Principales", fontsize=14, fontweight='bold')

    axes_flat = axes.flatten() if isinstance(axes, np.ndarray) else [axes]

    for idx, st_code in enumerate(estaciones_validas):
        ax = axes_flat[idx]
        data = datos_eventos_dict[st_code]
        meta = data['meta']
        times = data['times']
        channels = data['channels']

        # Seleccionar la componente con mayor PGA
        best_comp = max(channels.keys(), key=lambda c: np.max(np.abs(channels[c])))
        sig = channels[best_comp]
        sig_proc = signal.detrend(sig - np.mean(sig))
        if aplicar_filtro:
            sig_proc = aplicar_filtro_pasabanda(sig_proc, meta['fs_hz'], 0.1, 10.0)

        pga = np.max(np.abs(sig_proc))
        dist = meta.get('distancia_epicentral_km', 'N/A')

        ax.plot(times[:len(sig_proc)], sig_proc, color='#d62728', linewidth=0.7)
        ax.set_title(f"{st_code} ({best_comp}) | R={dist} km | PGA={pga:.2f} Gal", fontsize=9, fontweight='bold')
        ax.set_ylabel("Gal", fontsize=8)
        ax.grid(True, linestyle=':', alpha=0.5)

    # Ocultar ejes vacíos si los hay
    for idx in range(n_est, len(axes_flat)):
        axes_flat[idx].axis('off')

    for ax in axes_flat[-n_cols:]:
        ax.set_xlabel("Tiempo (s)", fontsize=9, fontweight='bold')

    plt.tight_layout(rect=[0, 0, 1, 0.95])

    if output_png:
        out_abs = os.path.abspath(output_png)
        os.makedirs(os.path.dirname(out_abs), exist_ok=True)
        fig.savefig(out_abs, bbox_inches='tight')
        print(f"Parrilla multi-estación guardada en: {out_abs}")
    plt.close(fig)

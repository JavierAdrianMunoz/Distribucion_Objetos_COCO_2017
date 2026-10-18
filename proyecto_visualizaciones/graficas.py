"""Construccion de las figuras del analisis exploratorio.

Cada funcion devuelve un objeto ``Figure`` independiente de la interfaz.
Asi la UI decide donde dibujarlo y los graficos se pueden reutilizar o
probar por separado.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("TkAgg")

import numpy as np
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.ticker import NullFormatter, PercentFormatter
import pandas as pd

from config import AZUL, GRIS, GRIS_CLARO, ROJO, TINTA


def _nueva_figura(ancho: float, alto: float) -> Figure:
    return Figure(figsize=(ancho, alto), dpi=100, facecolor="white")


def _preparar_eje(ax, titulo: str, subtitulo: str, xlabel: str, ylabel: str) -> None:
    ax.set_facecolor("white")
    ax.grid(True, color=GRIS_CLARO, linewidth=0.8)
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color("#CBD5E1")
    ax.tick_params(colors="#475569", labelsize=9)
    ax.set_title(subtitulo, loc="left", fontsize=9.5, color=GRIS, pad=10)
    ax.set_xlabel(xlabel, fontsize=10, color="#334155", labelpad=8)
    ax.set_ylabel(ylabel, fontsize=10, color="#334155", labelpad=8)
    ax.figure.suptitle(
        titulo,
        x=0.02,
        y=0.975,
        ha="left",
        fontsize=14,
        fontweight="bold",
        color=TINTA,
    )


def _densidad_kde(valores: np.ndarray, puntos: int = 420):
    """KDE gaussiano sencillo"""

    valores = np.asarray(valores, dtype=float)
    valores = valores[np.isfinite(valores)]
    if valores.size < 5:
        return None

    if valores.size > 25_000:
        generador = np.random.default_rng(7)
        valores = generador.choice(valores, 25_000, replace=False)

    desviacion = float(valores.std(ddof=1))
    q25, q75 = np.percentile(valores, [25, 75])
    iqr = float(q75 - q25)
    referencia = min(desviacion, iqr / 1.34) if iqr > 0 else desviacion
    ancho = 0.9 * referencia * valores.size ** (-0.2)
    if not np.isfinite(ancho) or ancho <= 0:
        return None

    grilla = np.linspace(float(valores.min()), float(valores.max()), puntos)
    densidad = np.zeros_like(grilla)
    for inicio in range(0, valores.size, 4_000):
        lote = valores[inicio : inicio + 4_000]
        z = (grilla[:, None] - lote[None, :]) / ancho
        densidad += np.exp(-0.5 * z * z).sum(axis=1)
    densidad /= valores.size * ancho * np.sqrt(2 * np.pi)
    return grilla, densidad


def histograma_x(df: pd.DataFrame, contexto: str = "") -> Figure:
    """Distribucion horizontal del centro de cada objeto."""

    datos = df["center_x_norm"].dropna().to_numpy()
    subtitulo = "COCO 2017 · centro X de cada bounding box, normalizado"
    if contexto:
        subtitulo += f" · {contexto}"

    figura = _nueva_figura(10.2, 5.8)
    ax = figura.add_subplot(111)
    _preparar_eje(
        ax,
        "Distribución horizontal de los objetos",
        subtitulo,
        "Centro horizontal normalizado (X)",
        "Porcentaje de anotaciones",
    )

    conteos, bordes = np.histogram(datos, bins=32)
    pesos = np.ones(datos.size) / datos.size
    ax.hist(
        datos,
        bins=bordes,
        weights=pesos,
        color=AZUL,
        alpha=0.32,
        edgecolor="white",
        linewidth=0.9,
        label="Anotaciones",
        zorder=2,
    )

    kde = _densidad_kde(datos)
    if kde is not None:
        grilla, densidad = kde
        ancho_bin = float(bordes[1] - bordes[0])
        ax.plot(
            grilla,
            densidad * ancho_bin,
            color=AZUL,
            linewidth=2.4,
            label="Densidad estimada",
            zorder=3,
        )

    mediana = float(np.median(datos))
    ax.axvline(
        0.5,
        color=ROJO,
        linestyle="--",
        linewidth=1.4,
        label="Centro de la imagen (50 %)",
        zorder=4,
    )
    ax.axvline(
        mediana,
        color="#0F766E",
        linestyle=":",
        linewidth=1.6,
        label=f"Mediana ({mediana:.1%})",
        zorder=4,
    )

    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    ax.set_xlim(0, 1)
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    figura.subplots_adjust(left=0.085, right=0.97, top=0.85, bottom=0.14)
    figura._interaccion = {
        "tipo": "histograma",
        "bordes": bordes,
        "conteos": conteos,
        "total": int(datos.size),
        "ayuda": (
            "Pasa el cursor por una barra para ver su rango y frecuencia · "
            "rueda: zoom · doble clic: restablecer"
        ),
    }
    return figura


def dispersion_espacial(df: pd.DataFrame, contexto: str = "") -> Figure:
    """Nube de puntos X vs. Y con los cuatro cuadrantes marcados."""

    subtitulo = (
        "Cada punto es una anotación; la transparencia revela la densidad"
    )
    if contexto:
        subtitulo += f" · {contexto}"

    figura = _nueva_figura(8.8, 7.6)
    ax = figura.add_subplot(111)
    _preparar_eje(
        ax,
        "Distribución espacial de los objetos",
        subtitulo,
        "Centro horizontal normalizado (X)",
        "Centro vertical normalizado (Y)",
    )

    ax.scatter(
        df["center_x_norm"],
        df["center_y_norm"],
        s=7,
        alpha=0.10,
        color=AZUL,
        edgecolors="none",
        rasterized=True,
        zorder=2,
    )
    ax.axvline(0.5, color=ROJO, linestyle="--", linewidth=1.2, alpha=0.85)
    ax.axhline(0.5, color=ROJO, linestyle="--", linewidth=1.2, alpha=0.85)

    etiquetas = [
        (0.03, 0.96, "Superior izquierda", "left", "top"),
        (0.97, 0.96, "Superior derecha", "right", "top"),
        (0.03, 0.04, "Inferior izquierda", "left", "bottom"),
        (0.97, 0.04, "Inferior derecha", "right", "bottom"),
    ]
    for x, y, texto, alineacion, vertical in etiquetas:
        ax.text(
            x,
            y,
            texto,
            transform=ax.transAxes,
            ha=alineacion,
            va=vertical,
            fontsize=8.5,
            color="#64748B",
            zorder=5,
        )

    ax.set_xlim(0, 1)
    ax.set_ylim(1, 0)
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    figura.subplots_adjust(left=0.11, right=0.97, top=0.85, bottom=0.135)
    figura._interaccion = {
        "tipo": "puntos",
        "datos": df[
            [
                "category",
                "image_id",
                "center_x_norm",
                "center_y_norm",
                "area_norm",
            ]
        ].reset_index(drop=True),
        "ayuda": (
            "Pasa el cursor por un punto · clic para fijar el detalle · "
            "rueda: zoom · doble clic: restablecer"
        ),
    }
    return figura


def dispersion_categorias(
    df: pd.DataFrame, top: int = 6, contexto: str = ""
) -> Figure:
    """Dispersion por categoria; el tamano codifica el area del objeto."""

    top_categorias = df["category"].value_counts().head(top).index.tolist()
    datos = df[df["category"].isin(top_categorias)].copy()

    etiqueta = (
        "1 categoría"
        if len(top_categorias) == 1
        else f"Top {len(top_categorias)} categorías"
    )
    subtitulo = (
        f"{etiqueta} · tamaño del punto proporcional al área del objeto"
    )
    if contexto:
        subtitulo += f" · {contexto}"

    figura = _nueva_figura(10.6, 7.6)
    ax = figura.add_subplot(111)
    _preparar_eje(
        ax,
        "Distribución por categoría y área",
        subtitulo,
        "Centro horizontal normalizado (X)",
        "Centro vertical normalizado (Y)",
    )

    colores = matplotlib.colormaps["tab10"].colors
    areas = datos["area_norm"].clip(lower=0)
    techo = float(areas.quantile(0.995)) or float(areas.max()) or 1.0
    tamanos = 12 + 210 * np.sqrt((areas / techo).clip(0, 1))

    for indice, categoria in enumerate(top_categorias):
        mascara = datos["category"] == categoria
        ax.scatter(
            datos.loc[mascara, "center_x_norm"],
            datos.loc[mascara, "center_y_norm"],
            s=tamanos[mascara],
            color=colores[indice % len(colores)],
            alpha=0.48,
            linewidths=0,
            label=categoria,
            zorder=2 + indice,
        )

    ax.axvline(0.5, color=GRIS, linestyle="--", alpha=0.30, linewidth=1)
    ax.axhline(0.5, color=GRIS, linestyle="--", alpha=0.30, linewidth=1)
    ax.set_xlim(0, 1)
    ax.set_ylim(1, 0)
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.yaxis.set_major_formatter(PercentFormatter(1))

    manijas_categoria = [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="",
            markersize=7,
            markerfacecolor=colores[i % len(colores)],
            markeredgecolor="none",
            label=categoria,
        )
        for i, categoria in enumerate(top_categorias)
    ]
    leyenda_categoria = ax.legend(
        handles=manijas_categoria,
        title="Categoría",
        title_fontsize=9,
        fontsize=9,
        frameon=False,
        loc="upper left",
        bbox_to_anchor=(1.01, 1.0),
    )
    ax.add_artist(leyenda_categoria)

    manijas_tamano = [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="",
            markersize=np.sqrt(tamano),
            markerfacecolor="#CBD5E1",
            markeredgecolor="#94A3B8",
            label=etiqueta,
        )
        for tamano, etiqueta in ((28, "Objeto pequeño"), (110, "Mediano"), (210, "Grande"))
    ]
    ax.legend(
        handles=manijas_tamano,
        title="Área",
        title_fontsize=9,
        fontsize=8.5,
        frameon=False,
        loc="lower left",
        bbox_to_anchor=(1.01, 0.0),
    )

    figura.subplots_adjust(left=0.10, right=0.80, top=0.85, bottom=0.135)
    figura._interaccion = {
        "tipo": "puntos",
        "datos": datos[
            [
                "category",
                "image_id",
                "center_x_norm",
                "center_y_norm",
                "area_norm",
            ]
        ].reset_index(drop=True),
        "ayuda": (
            "Pasa el cursor por un punto · clic para fijar el detalle · "
            "rueda: zoom · doble clic: restablecer"
        ),
    }
    return figura


def boxplot_areas(
    df: pd.DataFrame, top: int = 10, contexto: str = ""
) -> Figure:
    """Comparacion de areas normalizadas; escala logaritmica."""

    top_categorias = df["category"].value_counts().head(top).index.tolist()
    series = [
        df.loc[df["category"] == categoria, "area_norm"].dropna().to_numpy()
        for categoria in top_categorias
    ]
    series = [valores[valores > 0] for valores in series]

    subtitulo = (
        f"{len(top_categorias)} categorías · escala logarítmica · "
        "la caja representa el 50 % central"
    )
    if contexto:
        subtitulo += f" · {contexto}"

    figura = _nueva_figura(11.4, 6.4)
    ax = figura.add_subplot(111)
    _preparar_eje(
        ax,
        "Distribución del área por categoría",
        subtitulo,
        "Categoría",
        "Área normalizada (proporción de la imagen)",
    )

    colores = matplotlib.colormaps["tab10"].colors
    cajas = ax.boxplot(
        series,
        patch_artist=True,
        widths=0.62,
        showfliers=False,
        medianprops={"color": TINTA, "linewidth": 1.5},
        whiskerprops={"color": "#64748B", "linewidth": 1.0},
        capprops={"color": "#64748B", "linewidth": 1.0},
    )
    for parche, color in zip(cajas["boxes"], colores):
        parche.set_facecolor(color)
        parche.set_alpha(0.80)
        parche.set_edgecolor("#334155")
        parche.set_linewidth(0.9)

    ax.set_yscale("log")
    ax.set_xticks(range(1, len(top_categorias) + 1))
    ax.set_xticklabels(top_categorias, rotation=28, ha="right")
    ax.yaxis.set_minor_formatter(NullFormatter())
    figura.subplots_adjust(left=0.105, right=0.97, top=0.85, bottom=0.24)

    estadisticas = []
    for categoria, valores in zip(top_categorias, series):
        if valores.size == 0:
            continue
        q1, mediana, q3 = np.percentile(valores, [25, 50, 75])
        estadisticas.append(
            {
                "categoria": categoria,
                "n": int(valores.size),
                "q1": float(q1),
                "mediana": float(mediana),
                "q3": float(q3),
            }
        )
    figura._interaccion = {
        "tipo": "cajas",
        "estadisticas": estadisticas,
        "cajas": list(cajas["boxes"]),
        "ayuda": (
            "Pasa el cursor por una caja para ver sus estadísticas · "
            "rueda: zoom · doble clic: restablecer"
        ),
    }
    return figura

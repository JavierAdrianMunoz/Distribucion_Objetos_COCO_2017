"""Salidas del proyecto: CSV para Tableau e imagenes PNG."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import DIRECTORIO_SALIDAS, ruta_csv_salida
from datos import COLUMNAS_CSV


def exportar_csv(df: pd.DataFrame, ruta: str | Path | None = None) -> Path:
    """Escribe las columnas normalizadas y devuelve la ruta generada."""

    destino = Path(ruta) if ruta else ruta_csv_salida()
    destino.parent.mkdir(parents=True, exist_ok=True)
    df[COLUMNAS_CSV].to_csv(destino, index=False, encoding="utf-8-sig")
    return destino


def guardar_imagen(figura, ruta: str | Path) -> Path:
    """Guarda una figura de matplotlib en PNG """

    destino = Path(ruta)
    destino.parent.mkdir(parents=True, exist_ok=True)
    figura.savefig(destino, dpi=220, facecolor="white", bbox_inches="tight")
    return destino


def preparar_salidas() -> Path:
    """Crea la carpeta de salidas si aun no existe."""

    DIRECTORIO_SALIDAS.mkdir(parents=True, exist_ok=True)
    return DIRECTORIO_SALIDAS

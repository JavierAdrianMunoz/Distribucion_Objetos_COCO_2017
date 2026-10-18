"""Carga y preparacion de las anotaciones COCO."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from config import buscar_anotaciones

COLUMNAS_CSV = [
    "image_id",
    "category",
    "center_x_norm",
    "center_y_norm",
    "area_norm",
]


def _leer_json(ruta: Path) -> dict:
    with ruta.open("r", encoding="utf-8") as archivo:
        return json.load(archivo)


def cargar_datos(ruta: str | Path | None = None) -> pd.DataFrame:
    """Lee el JSON de COCO y devuelve las anotaciones normalizadas.

    Parametros
    ----------
    ruta:
        Archivo de anotaciones. Si se omite, se busca automaticamente.
    """

    archivo = Path(ruta).resolve() if ruta else buscar_anotaciones()
    if not archivo.exists():
        raise FileNotFoundError(f"No se encontro el archivo:\n{archivo}")

    coco = _leer_json(archivo)
    anotaciones = coco.get("annotations") or []
    if not anotaciones:
        raise ValueError("El archivo COCO no contiene anotaciones.")

    df = pd.DataFrame(anotaciones)
    columnas_utiles = ["id", "image_id", "category_id", "bbox", "area", "iscrowd"]
    df = df[[col for col in columnas_utiles if col in df.columns]].copy()

    bbox = pd.DataFrame(
        df["bbox"].tolist(),
        columns=["bbox_x", "bbox_y", "bbox_w", "bbox_h"],
        index=df.index,
    )
    df = pd.concat([df.drop(columns=["bbox"]), bbox], axis=1)

    imagenes = pd.DataFrame(coco.get("images") or [])[["id", "width", "height"]]
    df = df.merge(
        imagenes,
        left_on="image_id",
        right_on="id",
        suffixes=("", "_img"),
    )
    df = df.drop(columns=[col for col in ("id_img",) if col in df.columns])

    categorias = {c["id"]: c["name"] for c in coco.get("categories") or []}
    df["category"] = df["category_id"].map(categorias)

    df["x_norm"] = df["bbox_x"] / df["width"]
    df["y_norm"] = df["bbox_y"] / df["height"]
    df["w_norm"] = df["bbox_w"] / df["width"]
    df["h_norm"] = df["bbox_h"] / df["height"]
    df["area_norm"] = df["w_norm"] * df["h_norm"]
    df["area_px"] = df["bbox_w"] * df["bbox_h"]

    # Se conservan solo las cajas cuyo origen cae dentro de la imagen.
    df = df[
        df["x_norm"].between(0, 1) & df["y_norm"].between(0, 1)
    ].copy()

    df["center_x_norm"] = (df["bbox_x"] + df["bbox_w"] / 2) / df["width"]
    df["center_y_norm"] = (df["bbox_y"] + df["bbox_h"] / 2) / df["height"]

    if df.empty:
        raise ValueError("No quedaron anotaciones válidas después de la limpieza.")

    return df


def resumen_dataset(df: pd.DataFrame) -> dict:
    """Estadisticas basicas que alimentan la vista de informacion."""

    conteo = df["category"].value_counts()
    total = int(len(df))
    tabla = pd.DataFrame(
        {
            "categoria": conteo.index,
            "anotaciones": conteo.values,
        }
    )
    tabla["porcentaje"] = tabla["anotaciones"] / total * 100

    return {
        "anotaciones": total,
        "imagenes": int(df["image_id"].nunique()),
        "categorias": int(df["category"].nunique()),
        "categoria_mas_frecuente": str(conteo.index[0]),
        "top_categorias": tabla.head(10),
    }

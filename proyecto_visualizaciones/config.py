"""Rutas, constantes y colores compartidos por el proyecto."""

from __future__ import annotations

from pathlib import Path

# Raiz del proyecto
DIRECTORIO_PROYECTO = Path(__file__).resolve().parent
DIRECTORIO_SALIDAS = DIRECTORIO_PROYECTO / "salidas"

NOMBRE_ANOTACIONES = "instances_val2017.json"

# Colores usados por las graficas de matplotlib.
AZUL = "#2563EB"
ROJO = "#E11D48"
GRIS = "#64748B"
GRIS_CLARO = "#E2E8F0"
TINTA = "#0F172A"


def rutas_candidatas() -> list[Path]:
    """Rutas donde se busca el archivo de anotaciones, en orden de prioridad."""

    return [
        DIRECTORIO_PROYECTO.parent.parent / "dataset" / NOMBRE_ANOTACIONES,
        DIRECTORIO_PROYECTO.parent / "dataset" / NOMBRE_ANOTACIONES,
        DIRECTORIO_PROYECTO / "dataset" / NOMBRE_ANOTACIONES,
        Path.cwd() / "dataset" / NOMBRE_ANOTACIONES,
    ]


def buscar_anotaciones() -> Path:
    """Devuelve la primera ruta existente o lanza un error explicativo."""

    revisadas: list[Path] = []
    for candidata in rutas_candidatas():
        ruta = candidata.resolve()
        if ruta in revisadas:
            continue
        revisadas.append(ruta)
        if ruta.exists():
            return ruta

    detalle = "\n".join(f"  - {ruta}" for ruta in revisadas)
    raise FileNotFoundError(
        "No se encontró el archivo de anotaciones de COCO.\n\n"
        "Se revisaron estas rutas:\n"
        f"{detalle}\n\n"
        "Coloca 'instances_val2017.json' dentro de la carpeta 'dataset'."
    )


def ruta_csv_salida() -> Path:
    """Ruta por defecto del CSV que se abre en Tableau Public."""

    return DIRECTORIO_SALIDAS / "coco_visualizacion.csv"

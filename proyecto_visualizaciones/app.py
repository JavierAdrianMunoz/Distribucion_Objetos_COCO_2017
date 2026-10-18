from __future__ import annotations

import ctypes
import sys
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parent
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

from ui.ventana import VentanaPrincipal


def _activar_dpi() -> None:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


def main() -> None:
    _activar_dpi()
    aplicacion = VentanaPrincipal()
    aplicacion.ejecutar()


if __name__ == "__main__":
    main()

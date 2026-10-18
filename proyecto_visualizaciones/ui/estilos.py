"""Paleta y estilos ttk de la aplicacion."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

PALETA = {
    "fondo": "#F1F5F9",
    "sidebar": "#0B1220",
    "sidebar_hover": "#1E293B",
    "sidebar_activo": "#16233A",
    "acento": "#3B82F6",
    "acento_suave": "#DBEAFE",
    "texto": "#0F172A",
    "texto_tenue": "#64748B",
    "texto_claro": "#E2E8F0",
    "texto_claro_tenue": "#94A3B8",
    "tarjeta": "#FFFFFF",
    "borde": "#E2E8F0",
    "exito": "#059669",
    "error": "#DC2626",
    "aviso": "#D97706",
}

FUENTE = "Segoe UI"


def tipografia(tamano: int, peso: str = "normal") -> tuple:
    return (FUENTE, tamano, peso)


def configurar_estilos(raiz: tk.Misc) -> None:
    """Aplica un tema claro y coherente a los widgets ttk."""

    estilo = ttk.Style(raiz)
    try:
        estilo.theme_use("clam")
    except tk.TclError:
        pass

    estilo.configure(
        "Treeview",
        background="white",
        fieldbackground="white",
        foreground=PALETA["texto"],
        rowheight=30,
        borderwidth=0,
        font=tipografia(10),
    )
    estilo.configure(
        "Treeview.Heading",
        background="#F8FAFC",
        foreground=PALETA["texto_tenue"],
        font=tipografia(9, "bold"),
        borderwidth=0,
        padding=(10, 8),
    )
    estilo.map(
        "Treeview",
        background=[("selected", PALETA["acento_suave"])],
        foreground=[("selected", PALETA["texto"])],
    )
    estilo.map("Treeview.Heading", background=[("active", "#F1F5F9")])

    estilo.configure(
        "TProgressbar",
        troughcolor=PALETA["borde"],
        background=PALETA["acento"],
        bordercolor=PALETA["borde"],
        lightcolor=PALETA["acento"],
        darkcolor=PALETA["acento"],
        thickness=6,
    )

    estilo.configure(
        "Secundario.TButton",
        background="white",
        foreground=PALETA["texto"],
        bordercolor=PALETA["borde"],
        focusthickness=0,
        focuscolor="white",
        padding=(14, 8),
        font=tipografia(9),
    )
    estilo.map(
        "Secundario.TButton",
        background=[("active", "#F8FAFC"), ("disabled", "#F8FAFC")],
        foreground=[("disabled", "#94A3B8")],
        bordercolor=[("active", "#CBD5E1")],
    )

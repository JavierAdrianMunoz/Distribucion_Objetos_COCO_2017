"""Paneles que ocupan el area principal de la ventana."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from interaccion import conectar_interaccion
from ui.componentes import TarjetaEstadistica
from ui.estilos import PALETA, tipografia


class VistaGrafica(tk.Frame):
    """Tarjeta con controles, lienzo interactivo y barra de herramientas."""

    def __init__(self, maestro: tk.Misc) -> None:
        super().__init__(maestro, bg=PALETA["fondo"])
        self._marco = tk.Frame(
            self,
            bg="white",
            highlightbackground=PALETA["borde"],
            highlightthickness=1,
        )
        self._marco.pack(fill="both", expand=True)
        self._marco.grid_columnconfigure(0, weight=1)
        self._marco.grid_rowconfigure(1, weight=1)

        self.controles = tk.Frame(self._marco, bg="white")
        self.controles.grid(
            row=0, column=0, sticky="ew", padx=16, pady=(12, 8)
        )
        self.controles.grid_remove()

        self._zona = tk.Frame(self._marco, bg="white")
        self._zona.grid(row=1, column=0, sticky="nsew")

        self._zona_barra = tk.Frame(self._marco, bg="white")
        self._zona_barra.grid(row=2, column=0, sticky="ew")

        tk.Frame(self._marco, bg=PALETA["borde"], height=1).grid(
            row=3, column=0, sticky="ew"
        )

        pie = tk.Frame(self._marco, bg="#F8FAFC")
        pie.grid(row=4, column=0, sticky="ew")
        self._punto_lectura = tk.Label(
            pie,
            text="●",
            bg="#F8FAFC",
            fg="#94A3B8",
            font=tipografia(8),
        )
        self._punto_lectura.pack(side="left", padx=(14, 6), pady=7)
        self._lectura = tk.Label(
            pie,
            text="",
            bg="#F8FAFC",
            fg=PALETA["texto_tenue"],
            font=tipografia(9),
            anchor="w",
        )
        self._lectura.pack(
            side="left", fill="x", expand=True, padx=(0, 14), pady=7
        )

        self._canvas: FigureCanvasTkAgg | None = None
        self._barra: NavigationToolbar2Tk | None = None
        self.controlador = None
        self.figura = None

    def usar_controles(self) -> tk.Frame:
        self.controles.grid()
        return self.controles

    def limpiar_controles(self) -> None:
        for hijo in self.controles.winfo_children():
            hijo.destroy()
        self.controles.grid_remove()

    def mostrar(self, figura) -> None:
        if self._barra is not None:
            self._barra.destroy()
            self._barra = None
        if self._canvas is not None:
            self._canvas.get_tk_widget().destroy()
            self._canvas = None

        self.figura = figura
        self.controlador = None

        self._canvas = FigureCanvasTkAgg(figura, master=self._zona)
        self._barra = NavigationToolbar2Tk(
            self._canvas, self._zona_barra, pack_toolbar=False
        )
        self._barra.configure(background="white")
        for hijo in self._barra.winfo_children():
            try:
                hijo.configure(background="white")
            except tk.TclError:
                pass
        self._barra.update()
        self._barra.pack(fill="x")

        lienzo = self._canvas.get_tk_widget()
        lienzo.configure(bg="white", highlightthickness=0, cursor="crosshair")
        lienzo.pack(fill="both", expand=True)

        self.controlador = conectar_interaccion(
            figura, al_detalle=self.actualizar_lectura
        )
        metadatos = getattr(figura, "_interaccion", {})
        self.actualizar_lectura(
            metadatos.get(
                "ayuda",
                "Usa la barra inferior para hacer zoom o guardar la imagen.",
            ),
            "info",
        )
        self._canvas.draw_idle()

    def actualizar_lectura(self, texto: str, tono: str = "info") -> None:
        colores = {
            "info": "#94A3B8",
            "hover": PALETA["acento"],
            "seleccion": PALETA["error"],
        }
        self._punto_lectura.configure(fg=colores.get(tono, "#94A3B8"))
        self._lectura.configure(text=texto)


class VistaInfo(tk.Frame):
    """Resumen del dataset y tabla de categorias mas frecuentes."""

    def __init__(
        self,
        maestro: tk.Misc,
        df: pd.DataFrame,
        ruta: str,
        resumen: dict,
    ) -> None:
        super().__init__(maestro, bg=PALETA["fondo"])

        fila_tarjetas = tk.Frame(self, bg=PALETA["fondo"])
        fila_tarjetas.pack(fill="x", pady=(0, 18))
        for columna in range(4):
            fila_tarjetas.grid_columnconfigure(columna, weight=1, uniform="tarjetas")

        tarjetas = [
            ("Anotaciones", f"{resumen['anotaciones']:,}", PALETA["acento"], "Registros válidos"),
            ("Imágenes", f"{resumen['imagenes']:,}", "#0F766E", "Imágenes distintas"),
            ("Categorías", f"{resumen['categorias']:,}", "#7C3AED", "Clases de objeto"),
            (
                "Más frecuente",
                resumen["categoria_mas_frecuente"].capitalize(),
                "#D97706",
                "Categoría con más objetos",
            ),
        ]
        for indice, (etiqueta, valor, color, pie) in enumerate(tarjetas):
            tarjeta = TarjetaEstadistica(fila_tarjetas, valor, etiqueta, color)
            tarjeta.grid(
                row=0,
                column=indice,
                sticky="nsew",
                padx=(0 if indice == 0 else 8, 0),
            )
            tk.Label(
                tarjeta,
                text=pie,
                bg=PALETA["tarjeta"],
                fg="#94A3B8",
                font=tipografia(8),
                anchor="w",
            ).pack(fill="x", padx=18, pady=(0, 12))

        tarjeta_tabla = tk.Frame(
            self,
            bg="white",
            highlightbackground=PALETA["borde"],
            highlightthickness=1,
        )
        tarjeta_tabla.pack(fill="both", expand=True)

        cabecera = tk.Frame(tarjeta_tabla, bg="white")
        cabecera.pack(fill="x", padx=20, pady=(16, 10))
        tk.Label(
            cabecera,
            text="Categorías más frecuentes",
            bg="white",
            fg=PALETA["texto"],
            font=tipografia(12, "bold"),
            anchor="w",
        ).pack(anchor="w")
        tk.Label(
            cabecera,
            text=f"Archivo de anotaciones: {ruta}",
            bg="white",
            fg=PALETA["texto_tenue"],
            font=tipografia(9),
            anchor="w",
        ).pack(anchor="w", pady=(3, 0))

        contenedor = tk.Frame(tarjeta_tabla, bg="white")
        contenedor.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        tabla = ttk.Treeview(
            contenedor,
            columns=("categoria", "anotaciones", "porcentaje"),
            show="headings",
            height=10,
            selectmode="browse",
        )
        tabla.heading("categoria", text="Categoría", anchor="w")
        tabla.heading("anotaciones", text="Anotaciones", anchor="e")
        tabla.heading("porcentaje", text="% del total", anchor="e")
        tabla.column("categoria", anchor="w", width=320)
        tabla.column("anotaciones", anchor="e", width=140)
        tabla.column("porcentaje", anchor="e", width=110)
        tabla.tag_configure("par", background="#F8FAFC")
        tabla.tag_configure("impar", background="white")

        for indice, fila in resumen["top_categorias"].iterrows():
            tabla.insert(
                "",
                "end",
                values=(
                    str(fila["categoria"]).capitalize(),
                    f"{int(fila['anotaciones']):,}",
                    f"{fila['porcentaje']:.1f} %",
                ),
                tags=("par" if indice % 2 == 0 else "impar",),
            )

        barra = ttk.Scrollbar(contenedor, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=barra.set)
        tabla.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")


class VistaCarga(tk.Frame):
    """Pantalla de espera mientras se leen las anotaciones."""

    def __init__(self, maestro: tk.Misc) -> None:
        super().__init__(maestro, bg=PALETA["fondo"])

        centro = tk.Frame(self, bg=PALETA["fondo"])
        centro.place(relx=0.5, rely=0.45, anchor="center")

        tk.Label(
            centro,
            text="Cargando anotaciones de COCO",
            bg=PALETA["fondo"],
            fg=PALETA["texto"],
            font=tipografia(16, "bold"),
        ).pack()
        tk.Label(
            centro,
            text="Preparando bounding boxes y coordenadas normalizadas...",
            bg=PALETA["fondo"],
            fg=PALETA["texto_tenue"],
            font=tipografia(9),
        ).pack(pady=(6, 18))

        self.barra = ttk.Progressbar(centro, mode="indeterminate", length=280)
        self.barra.pack()
        self.barra.start(12)


class VistaError(tk.Frame):
    """Mensaje claro cuando no se pueden cargar los datos."""

    def __init__(self, maestro: tk.Misc, mensaje: str, al_reintentar) -> None:
        super().__init__(maestro, bg=PALETA["fondo"])

        tarjeta = tk.Frame(
            self,
            bg="white",
            highlightbackground=PALETA["borde"],
            highlightthickness=1,
        )
        tarjeta.place(relx=0.5, rely=0.45, anchor="center", relwidth=0.72)

        interior = tk.Frame(tarjeta, bg="white")
        interior.pack(fill="both", expand=True, padx=32, pady=28)

        tk.Label(
            interior,
            text="No se pudieron cargar los datos",
            bg="white",
            fg=PALETA["error"],
            font=tipografia(14, "bold"),
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            interior,
            text=mensaje,
            bg="white",
            fg=PALETA["texto_tenue"],
            font=tipografia(9),
            justify="left",
            anchor="w",
            wraplength=680,
        ).pack(fill="x", pady=(10, 20))

        ttk.Button(
            interior,
            text="Reintentar",
            style="Secundario.TButton",
            command=al_reintentar,
        ).pack(anchor="w")

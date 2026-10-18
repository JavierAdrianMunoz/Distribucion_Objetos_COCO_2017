"""Barra lateral con la marca, el resumen y las opciones de navegacion."""

from __future__ import annotations

import tkinter as tk

from ui.componentes import BotonMenu
from ui.estilos import PALETA, tipografia

OPCIONES_GRAFICAS = [
    ("histograma", "Histograma de X"),
    ("dispersion", "Dispersión espacial"),
    ("categorias", "Categoría y área"),
    ("boxplot", "Boxplot de área"),
]


class BarraLateral(tk.Frame):
    """Menu de navegacion; no conoce los datos ni las figuras."""

    def __init__(
        self,
        maestro: tk.Misc,
        al_seleccionar,
        al_exportar_csv,
        al_salir,
    ) -> None:
        super().__init__(maestro, bg=PALETA["sidebar"], width=272)
        self.pack_propagate(False)
        self._al_seleccionar = al_seleccionar
        self.botones: dict[str, BotonMenu] = {}
        self._construir(al_exportar_csv, al_salir)

    def _construir(self, al_exportar_csv, al_salir) -> None:
        marca = tk.Frame(self, bg=PALETA["sidebar"])
        marca.pack(fill="x", padx=22, pady=(26, 6))

        tk.Label(
            marca,
            text="COCO 2017",
            bg=PALETA["sidebar"],
            fg="#FFFFFF",
            font=tipografia(19, "bold"),
            anchor="w",
        ).pack(anchor="w")
        tk.Label(
            marca,
            text="Explorador de visualizaciones",
            bg=PALETA["sidebar"],
            fg=PALETA["texto_claro_tenue"],
            font=tipografia(9),
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        self.lbl_resumen = tk.Label(
            self,
            text="Cargando dataset...",
            bg=PALETA["sidebar"],
            fg="#64748B",
            font=tipografia(9),
            anchor="w",
            justify="left",
        )
        self.lbl_resumen.pack(fill="x", padx=22, pady=(10, 16))

        tk.Frame(self, bg="#1E293B", height=1).pack(
            fill="x", padx=22, pady=(0, 14)
        )

        self._seccion("VISUALIZACIONES")
        for clave, texto in OPCIONES_GRAFICAS:
            self._agregar_boton(
                clave,
                texto,
                lambda c=clave: self._al_seleccionar(c),
            )

        self._seccion("DATOS")
        self._agregar_boton(
            "info",
            "Información del dataset",
            lambda: self._al_seleccionar("info"),
        )
        self._agregar_boton("csv", "Exportar CSV", al_exportar_csv)

        tk.Frame(self, bg=PALETA["sidebar"]).pack(fill="both", expand=True)
        self._agregar_boton("salir", "Salir", al_salir, habilitado=True)
        self.botones["salir"].pack_configure(pady=(0, 18))

    def _agregar_boton(
        self,
        clave: str,
        texto: str,
        comando,
        habilitado: bool = False,
    ) -> None:
        boton = BotonMenu(self, texto, comando)
        boton.pack(fill="x", padx=10, pady=1)
        boton.habilitar(habilitado)
        self.botones[clave] = boton

    def _seccion(self, texto: str) -> None:
        tk.Label(
            self,
            text=texto,
            bg=PALETA["sidebar"],
            fg="#475569",
            font=tipografia(8, "bold"),
            anchor="w",
        ).pack(fill="x", padx=25, pady=(6, 6))

    def habilitar_datos(self, habilitado: bool) -> None:
        for clave in ("histograma", "dispersion", "categorias", "boxplot", "info", "csv"):
            self.botones[clave].habilitar(habilitado)

    def actualizar_resumen(self, resumen: dict) -> None:
        self.lbl_resumen.configure(
            text=(
                f"{resumen['anotaciones']:,} anotaciones\n"
                f"{resumen['imagenes']:,} imágenes · "
                f"{resumen['categorias']} categorías"
            )
        )

    def marcar_activo(self, clave: str) -> None:
        for nombre, boton in self.botones.items():
            boton.marcar_activo(nombre == clave)

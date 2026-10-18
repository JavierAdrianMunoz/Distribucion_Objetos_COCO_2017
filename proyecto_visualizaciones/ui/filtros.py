"""Panel de filtros por categoria y area para las vistas de dispersion."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ui.estilos import PALETA, tipografia

TODAS_LAS_CATEGORIAS = "Todas las categorías"


class PanelFiltros(tk.Frame):
    """Controles de filtrado con aviso diferido para no redibujar de mas."""

    def __init__(
        self,
        maestro: tk.Misc,
        categorias: list[str],
        categoria: str,
        percentil: int,
        al_cambiar,
    ) -> None:
        super().__init__(maestro, bg="white")
        self._al_cambiar = al_cambiar
        self._pendiente = None
        self._percentil_visible = int(percentil)

        tk.Label(
            self,
            text="Categoría",
            bg="white",
            fg=PALETA["texto_tenue"],
            font=tipografia(9),
        ).pack(side="left")

        valores = [TODAS_LAS_CATEGORIAS] + sorted(categorias)
        self.combo = ttk.Combobox(
            self,
            values=valores,
            state="readonly",
            width=23,
            font=tipografia(9),
        )
        self.combo.set(categoria)
        self.combo.pack(side="left", padx=(6, 16))
        self.combo.bind("<<ComboboxSelected>>", lambda _e: self._programar())

        tk.Label(
            self,
            text="Área mínima",
            bg="white",
            fg=PALETA["texto_tenue"],
            font=tipografia(9),
        ).pack(side="left")

        self.escala = ttk.Scale(
            self,
            from_=0,
            to=95,
            orient="horizontal",
            length=120,
            command=self._al_mover_escala,
        )
        self.escala.pack(side="left", padx=(6, 4))

        self.lbl_percentil = tk.Label(
            self,
            text=f"P{int(percentil)}",
            width=3,
            bg="white",
            fg=PALETA["texto"],
            font=tipografia(9, "bold"),
            anchor="w",
        )
        self.lbl_percentil.pack(side="left", padx=(0, 12))
        self.escala.set(percentil)

        ttk.Button(
            self,
            text="Restablecer",
            style="Secundario.TButton",
            command=self.restablecer,
        ).pack(side="left")

        self.lbl_conteo = tk.Label(
            self,
            text="",
            bg="white",
            fg=PALETA["texto_tenue"],
            font=tipografia(9),
        )
        self.lbl_conteo.pack(side="right")

    def _al_mover_escala(self, valor) -> None:
        percentil = int(round(float(valor)))
        self.lbl_percentil.configure(text=f"P{percentil}")
        if percentil == self._percentil_visible:
            return
        self._percentil_visible = percentil
        self._programar()

    def _programar(self) -> None:
        if self._pendiente is not None:
            self.after_cancel(self._pendiente)
        self._pendiente = self.after(220, self._emitir)

    def _emitir(self) -> None:
        self._pendiente = None
        percentil = int(round(float(self.escala.get())))
        self._al_cambiar(self.combo.get(), percentil)

    def restablecer(self) -> None:
        self.combo.set(TODAS_LAS_CATEGORIAS)
        self.escala.set(0)
        self._percentil_visible = 0
        self.lbl_percentil.configure(text="P0")
        self._programar()

    def actualizar_conteo(self, texto: str) -> None:
        self.lbl_conteo.configure(text=texto)

    def cancelar(self) -> None:
        if self._pendiente is not None:
            self.after_cancel(self._pendiente)
            self._pendiente = None

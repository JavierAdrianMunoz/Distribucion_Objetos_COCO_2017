"""Widgets reutilizables: botones del menu y tarjetas de estadisticas."""

from __future__ import annotations

import tkinter as tk

from ui.estilos import PALETA, tipografia


class BotonMenu(tk.Frame):
    """Boton plano de la barra lateral con barra de acento y estados."""

    def __init__(self, maestro: tk.Misc, texto: str, comando) -> None:
        super().__init__(maestro, bg=PALETA["sidebar"], cursor="hand2")
        self._comando = comando
        self._activo = False
        self._habilitado = True

        self._barra = tk.Frame(self, width=3, bg=PALETA["sidebar"])
        self._barra.pack(side="left", fill="y")

        self._etiqueta = tk.Label(
            self,
            text=texto,
            bg=PALETA["sidebar"],
            fg=PALETA["texto_claro_tenue"],
            activebackground=PALETA["sidebar"],
            font=tipografia(10),
            anchor="w",
            padx=15,
            pady=8,
            cursor="hand2",
        )
        self._etiqueta.pack(side="left", fill="both", expand=True)

        for widget in (self, self._barra, self._etiqueta):
            widget.bind("<Button-1>", self._al_clic)
            widget.bind("<Enter>", self._al_entrar)
            widget.bind("<Leave>", self._al_salir)

    def _al_clic(self, _evento=None) -> None:
        if self._habilitado:
            self._comando()

    def _al_entrar(self, _evento=None) -> None:
        if self._habilitado and not self._activo:
            self._pintar(PALETA["sidebar_hover"], PALETA["texto_claro"])

    def _al_salir(self, _evento=None) -> None:
        if self._activo:
            self._pintar(PALETA["sidebar_activo"], "#FFFFFF")
        elif self._habilitado:
            self._pintar(PALETA["sidebar"], PALETA["texto_claro_tenue"])
        else:
            self._pintar(PALETA["sidebar"], "#475569")

    def _pintar(self, fondo: str, color_texto: str) -> None:
        self.configure(bg=fondo)
        self._etiqueta.configure(bg=fondo, fg=color_texto)
        self._barra.configure(bg=PALETA["acento"] if self._activo else fondo)

    def marcar_activo(self, activo: bool) -> None:
        self._activo = activo
        if activo:
            self._pintar(PALETA["sidebar_activo"], "#FFFFFF")
            self._barra.configure(bg=PALETA["acento"])
        else:
            self._pintar(PALETA["sidebar"], PALETA["texto_claro_tenue"])

    def habilitar(self, habilitado: bool) -> None:
        self._habilitado = habilitado
        if habilitado:
            self._pintar(PALETA["sidebar"], PALETA["texto_claro_tenue"])
            self.configure(cursor="hand2")
            self._etiqueta.configure(cursor="hand2")
        else:
            self._pintar(PALETA["sidebar"], "#475569")
            self.configure(cursor="arrow")
            self._etiqueta.configure(cursor="arrow")


class TarjetaEstadistica(tk.Frame):
    """Tarjeta blanca con un numero grande y una etiqueta."""

    def __init__(
        self,
        maestro: tk.Misc,
        valor: str,
        etiqueta: str,
        acento: str = PALETA["acento"],
    ) -> None:
        super().__init__(
            maestro,
            bg=PALETA["tarjeta"],
            highlightbackground=PALETA["borde"],
            highlightthickness=1,
        )
        tk.Frame(self, bg=acento, height=3).pack(fill="x")

        cuerpo = tk.Frame(self, bg=PALETA["tarjeta"])
        cuerpo.pack(fill="both", expand=True, padx=18, pady=14)

        self.valor = tk.Label(
            cuerpo,
            text=valor,
            bg=PALETA["tarjeta"],
            fg=PALETA["texto"],
            font=tipografia(21, "bold"),
            anchor="w",
        )
        self.valor.pack(fill="x")
        tk.Label(
            cuerpo,
            text=etiqueta,
            bg=PALETA["tarjeta"],
            fg=PALETA["texto_tenue"],
            font=tipografia(9),
            anchor="w",
        ).pack(fill="x", pady=(2, 0))

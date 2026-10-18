"""Interactividad de las figuras: hover, clic y zoom con la rueda.

Cada funcion que construye una figura deja metadatos en
``figura._interaccion``. Este modulo los lee y conecta los eventos de
matplotlib con la interfaz.
"""

from __future__ import annotations

import numpy as np

COLOR_ACCENTO = "#E11D48"
COLOR_TEXTO = "#0F172A"
COLOR_BORDE = "#334155"
DISTANCIA_MAXIMA = 14  # pixeles para considerar que el cursor toca un punto

ESTILO_TOOLTIP = {
    "boxstyle": "round,pad=0.42",
    "facecolor": "white",
    "edgecolor": "#CBD5E1",
    "linewidth": 0.8,
    "alpha": 0.97,
}


def _sin_efecto(*_argumentos, **_opciones) -> None:
    return None


class _Controlador:
    """Base comun: tooltip, zoom con rueda y doble clic para restablecer."""

    def __init__(
        self, figura, ax, ayuda: str, al_detalle, usar_blit: bool = False
    ) -> None:
        self.figura = figura
        self.ax = ax
        self.ayuda = ayuda
        self._al_detalle = al_detalle or _sin_efecto
        self._texto_fijado = ""
        self._limites_iniciales = (tuple(ax.get_xlim()), tuple(ax.get_ylim()))
        self._usar_blit = usar_blit
        self._fondo = None

        self._tooltip = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(14, 14),
            textcoords="offset points",
            fontsize=9,
            color=COLOR_TEXTO,
            bbox=ESTILO_TOOLTIP,
            annotation_clip=False,
            zorder=50,
        )
        self._tooltip.set_visible(False)
        self._tooltip.set_animated(usar_blit)

        lienzo = figura.canvas
        lienzo.mpl_connect("scroll_event", self._rueda)
        lienzo.mpl_connect("button_press_event", self._doble_clic)
        lienzo.mpl_connect("figure_leave_event", self._salir)
        lienzo.mpl_connect("axes_leave_event", self._salir)
        if usar_blit:
            lienzo.mpl_connect("draw_event", self._al_dibujar)

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    def _modo_navegacion(self) -> bool:
        barra = getattr(self.figura.canvas, "toolbar", None)
        return bool(getattr(barra, "mode", ""))

    def _al_dibujar(self, _evento) -> None:
        try:
            self._fondo = self.figura.canvas.copy_from_bbox(self.figura.bbox)
        except Exception:
            self._fondo = None

    def _dibujar_extras(self) -> None:
        return None

    def _pintar_capa(self) -> None:
        """Redibuja solo la capa interactiva cuando es posible."""

        lienzo = self.figura.canvas
        if not self._usar_blit or self._fondo is None:
            lienzo.draw_idle()
            return

        try:
            lienzo.restore_region(self._fondo)
            if self._tooltip.get_visible():
                self.ax.draw_artist(self._tooltip)
            self._dibujar_extras()
            lienzo.blit(self.figura.bbox)
        except Exception:
            self._fondo = None
            lienzo.draw_idle()

    def _mostrar_tooltip(self, x: float, y: float, texto: str) -> None:
        # Coloca el aviso hacia dentro de la figura para no cortarlo.
        px, py = self.ax.transData.transform((x, y))
        x0, y0, ancho, alto = self.ax.bbox.bounds
        derecha = px > x0 + 0.68 * ancho
        arriba = py > y0 + 0.80 * alto
        self._tooltip.xyann = (
            -14 if derecha else 14,
            -14 if arriba else 14,
        )
        self._tooltip.set_ha("right" if derecha else "left")
        self._tooltip.set_va("top" if arriba else "bottom")

        self._tooltip.xy = (x, y)
        self._tooltip.set_text(texto)
        self._tooltip.set_visible(True)
        self._pintar_capa()

    def _ocultar_tooltip(self) -> None:
        if self._tooltip.get_visible():
            self._tooltip.set_visible(False)
            self._pintar_capa()

    def _restaurar_lectura(self) -> None:
        if self._texto_fijado:
            self._al_detalle(self._texto_fijado, "seleccion")
        else:
            self._al_detalle(self.ayuda, "info")

    def _salir(self, _evento=None) -> None:
        self._ocultar_tooltip()
        self._restaurar_lectura()

    def _fijar_texto(self, texto: str, tono: str = "seleccion") -> None:
        self._texto_fijado = texto
        self._al_detalle(texto, tono)

    # ------------------------------------------------------------------
    # Zoom
    # ------------------------------------------------------------------
    def _rueda(self, evento) -> None:
        if (
            evento.inaxes is not self.ax
            or evento.xdata is None
            or evento.ydata is None
            or self._modo_navegacion()
        ):
            return

        factor = 0.80 if evento.button == "up" else 1.25
        x0, x1 = self.ax.get_xlim()
        y0, y1 = self.ax.get_ylim()

        nuevo_x0 = evento.xdata - (evento.xdata - x0) * factor
        nuevo_x1 = evento.xdata + (x1 - evento.xdata) * factor
        nuevo_y0 = evento.ydata - (evento.ydata - y0) * factor
        nuevo_y1 = evento.ydata + (y1 - evento.ydata) * factor

        x_min, x_max = sorted(self._limites_iniciales[0])
        y_min, y_max = sorted(self._limites_iniciales[1])
        nuevo_x0 = min(max(nuevo_x0, x_min), x_max)
        nuevo_x1 = min(max(nuevo_x1, x_min), x_max)
        nuevo_y0 = min(max(nuevo_y0, y_min), y_max)
        nuevo_y1 = min(max(nuevo_y1, y_min), y_max)

        if abs(nuevo_x1 - nuevo_x0) < 1e-9 or abs(nuevo_y1 - nuevo_y0) < 1e-12:
            return

        self.ax.set_xlim(nuevo_x0, nuevo_x1)
        self.ax.set_ylim(nuevo_y0, nuevo_y1)
        self.figura.canvas.draw_idle()

    def _doble_clic(self, evento) -> None:
        if not getattr(evento, "dblclick", False) or evento.inaxes is not self.ax:
            return
        self.ax.set_xlim(self._limites_iniciales[0])
        self.ax.set_ylim(self._limites_iniciales[1])
        self._ocultar_tooltip()
        self._restaurar_lectura()
        self.figura.canvas.draw_idle()


class InteraccionPuntos(_Controlador):
    """Hover con detalle, seleccion con clic y zoom para nubes de puntos."""

    def __init__(self, figura, ax, datos, al_detalle, ayuda: str) -> None:
        super().__init__(figura, ax, ayuda, al_detalle, usar_blit=True)
        self.datos = datos.reset_index(drop=True)
        self._x = self.datos["center_x_norm"].to_numpy(dtype=float)
        self._y = self.datos["center_y_norm"].to_numpy(dtype=float)
        self._indice_hover = -1
        self._indice_fijado = -1

        self._marcador = ax.scatter(
            [],
            [],
            s=130,
            facecolors="none",
            edgecolors=COLOR_ACCENTO,
            linewidths=1.8,
            zorder=25,
            clip_on=False,
        )
        self._marcador.set_visible(False)
        self._marcador.set_animated(True)

        self.figura.canvas.mpl_connect("motion_notify_event", self._mover)
        self.figura.canvas.mpl_connect("button_press_event", self._clic)
        self._restaurar_lectura()

    def _dibujar_extras(self) -> None:
        if self._marcador.get_visible():
            self.ax.draw_artist(self._marcador)

    def _salir(self, evento=None) -> None:
        self._indice_hover = -1
        super()._salir(evento)

    def _mas_cercano(self, evento):
        if self._x.size == 0:
            return -1, float("inf")
        pixeles = self.ax.transData.transform(
            np.column_stack((self._x, self._y))
        )
        distancias = np.sum(
            (pixeles - np.array([evento.x, evento.y])) ** 2, axis=1
        )
        indice = int(np.argmin(distancias))
        return indice, float(distancias[indice])

    def _texto(self, fila) -> str:
        return (
            f"{fila['category']} · imagen {int(fila['image_id'])} · "
            f"X {fila['center_x_norm']:.1%} · "
            f"Y {fila['center_y_norm']:.1%} · "
            f"área {fila['area_norm']:.2%}"
        )

    def _mover(self, evento) -> None:
        if (
            evento.inaxes is not self.ax
            or evento.x is None
            or self._modo_navegacion()
        ):
            return

        indice, distancia = self._mas_cercano(evento)
        if distancia > DISTANCIA_MAXIMA**2:
            if self._indice_hover >= 0:
                self._indice_hover = -1
                self._ocultar_tooltip()
                self._restaurar_lectura()
            return

        if indice == self._indice_hover:
            return

        self._indice_hover = indice
        fila = self.datos.iloc[indice]
        texto = self._texto(fila)
        self._mostrar_tooltip(
            float(fila["center_x_norm"]),
            float(fila["center_y_norm"]),
            texto,
        )
        self._al_detalle(texto, "hover")

    def _clic(self, evento) -> None:
        if (
            evento.inaxes is not self.ax
            or evento.button != 1
            or getattr(evento, "dblclick", False)
            or self._modo_navegacion()
        ):
            return

        indice, distancia = self._mas_cercano(evento)
        if distancia > DISTANCIA_MAXIMA**2:
            self._indice_fijado = -1
            self._texto_fijado = ""
            self._marcador.set_visible(False)
            self._restaurar_lectura()
            self._pintar_capa()
            return

        self._indice_fijado = indice
        fila = self.datos.iloc[indice]
        texto = self._texto(fila)
        self._marcador.set_offsets(
            [[float(fila["center_x_norm"]), float(fila["center_y_norm"])]]
        )
        self._marcador.set_visible(True)
        self._fijar_texto(texto)
        self._pintar_capa()


class InteraccionHistograma(_Controlador):
    """Muestra rango y frecuencia de la barra bajo el cursor."""

    def __init__(
        self, figura, ax, bordes, conteos, total, al_detalle, ayuda: str
    ) -> None:
        super().__init__(figura, ax, ayuda, al_detalle)
        self._bordes = np.asarray(bordes, dtype=float)
        self._conteos = np.asarray(conteos, dtype=int)
        self._total = max(int(total), 1)
        self._parches = list(ax.patches)
        self._indice = -1
        self._texto_actual = ""

        self.figura.canvas.mpl_connect("motion_notify_event", self._mover)
        self.figura.canvas.mpl_connect("button_press_event", self._clic)
        self._restaurar_lectura()

    def _mover(self, evento) -> None:
        if (
            evento.inaxes is not self.ax
            or evento.xdata is None
            or self._modo_navegacion()
        ):
            return

        if not self._bordes[0] <= evento.xdata <= self._bordes[-1]:
            self._limpiar()
            return

        indice = int(
            np.searchsorted(self._bordes, evento.xdata, side="right") - 1
        )
        indice = max(0, min(indice, len(self._conteos) - 1))
        if indice == self._indice:
            return

        self._indice = indice
        for posicion, parche in enumerate(self._parches):
            parche.set_alpha(0.55 if posicion == indice else 0.32)

        porcentaje = self._conteos[indice] / self._total
        texto = (
            f"{self._bordes[indice]:.1%} – {self._bordes[indice + 1]:.1%} · "
            f"{self._conteos[indice]:,} anotaciones ({porcentaje:.1%})"
        )
        self._texto_actual = texto
        x = float((self._bordes[indice] + self._bordes[indice + 1]) / 2)
        y = float(self._parches[indice].get_height())
        self._mostrar_tooltip(x, y, texto)
        self._al_detalle(texto, "hover")

    def _limpiar(self) -> None:
        if self._indice < 0:
            return
        self._indice = -1
        for parche in self._parches:
            parche.set_alpha(0.32)
        self._tooltip.set_visible(False)
        self._restaurar_lectura()
        self.figura.canvas.draw_idle()

    def _clic(self, evento) -> None:
        if (
            evento.inaxes is not self.ax
            or evento.button != 1
            or getattr(evento, "dblclick", False)
            or self._modo_navegacion()
        ):
            return
        if self._texto_actual:
            self._fijar_texto(self._texto_actual)

    def _salir(self, _evento=None) -> None:
        self._limpiar()


class InteraccionCajas(_Controlador):
    """Muestra estadisticas de la caja bajo el cursor."""

    def __init__(
        self, figura, ax, estadisticas, cajas, al_detalle, ayuda: str
    ) -> None:
        super().__init__(figura, ax, ayuda, al_detalle)
        self._estadisticas = estadisticas
        self._cajas = cajas
        self._indice = -1
        self._texto_actual = ""

        self.figura.canvas.mpl_connect("motion_notify_event", self._mover)
        self.figura.canvas.mpl_connect("button_press_event", self._clic)
        self._restaurar_lectura()

    def _mover(self, evento) -> None:
        if (
            evento.inaxes is not self.ax
            or evento.xdata is None
            or self._modo_navegacion()
        ):
            return

        indice = int(round(evento.xdata)) - 1
        if (
            not 0 <= indice < len(self._estadisticas)
            or indice >= len(self._cajas)
            or abs(evento.xdata - (indice + 1)) > 0.45
        ):
            self._limpiar()
            return

        if indice == self._indice:
            return

        self._indice = indice
        for posicion, caja in enumerate(self._cajas):
            if posicion == indice:
                caja.set_edgecolor(COLOR_ACCENTO)
                caja.set_linewidth(2.2)
            else:
                caja.set_edgecolor(COLOR_BORDE)
                caja.set_linewidth(0.9)

        datos = self._estadisticas[indice]
        texto = (
            f"{datos['categoria']} · n={datos['n']:,} · "
            f"mediana {datos['mediana']:.2%} · "
            f"Q1 {datos['q1']:.2%} · Q3 {datos['q3']:.2%}"
        )
        self._texto_actual = texto
        self._mostrar_tooltip(
            indice + 1, float(datos["mediana"]), texto
        )
        self._al_detalle(texto, "hover")

    def _limpiar(self) -> None:
        if self._indice < 0:
            return
        self._indice = -1
        for caja in self._cajas:
            caja.set_edgecolor(COLOR_BORDE)
            caja.set_linewidth(0.9)
        self._tooltip.set_visible(False)
        self._restaurar_lectura()
        self.figura.canvas.draw_idle()

    def _clic(self, evento) -> None:
        if (
            evento.inaxes is not self.ax
            or evento.button != 1
            or getattr(evento, "dblclick", False)
            or self._modo_navegacion()
        ):
            return
        if self._texto_actual:
            self._fijar_texto(self._texto_actual)

    def _salir(self, _evento=None) -> None:
        self._limpiar()


def conectar_interaccion(figura, al_detalle=None):
    """Crea el controlador adecuado segun los metadatos de la figura."""

    metadatos = getattr(figura, "_interaccion", None)
    if not metadatos:
        return None

    ax = figura.axes[0]
    ayuda = metadatos.get("ayuda", "")
    tipo = metadatos.get("tipo")

    if tipo == "puntos":
        return InteraccionPuntos(
            figura, ax, metadatos["datos"], al_detalle, ayuda
        )
    if tipo == "histograma":
        return InteraccionHistograma(
            figura,
            ax,
            metadatos["bordes"],
            metadatos["conteos"],
            metadatos["total"],
            al_detalle,
            ayuda,
        )
    if tipo == "cajas":
        return InteraccionCajas(
            figura,
            ax,
            metadatos["estadisticas"],
            metadatos["cajas"],
            al_detalle,
            ayuda,
        )
    return None

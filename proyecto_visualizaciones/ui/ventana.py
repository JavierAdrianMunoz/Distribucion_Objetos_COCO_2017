"""Ventana principal de la aplicacion."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from config import buscar_anotaciones
from datos import cargar_datos, resumen_dataset
from exportacion import exportar_csv, guardar_imagen, preparar_salidas
from graficas import (
    boxplot_areas,
    dispersion_categorias,
    dispersion_espacial,
    histograma_x,
)
from ui.barra_lateral import BarraLateral
from ui.estilos import PALETA, configurar_estilos, tipografia
from ui.filtros import TODAS_LAS_CATEGORIAS, PanelFiltros
from ui.vistas import VistaCarga, VistaError, VistaGrafica, VistaInfo

VISTAS = {
    "histograma": {
        "titulo": "Histograma de X",
        "subtitulo": "Distribución horizontal del centro de los objetos en COCO 2017",
        "constructor": histograma_x,
        "archivo": "histograma_x_coco.png",
    },
    "dispersion": {
        "titulo": "Dispersión espacial",
        "subtitulo": "Posición del centro de cada anotación dentro de su imagen",
        "constructor": dispersion_espacial,
        "archivo": "dispersion_espacial_coco.png",
    },
    "categorias": {
        "titulo": "Categoría y área",
        "subtitulo": "Dispersión por categoría; el tamaño del punto representa el área",
        "constructor": dispersion_categorias,
        "archivo": "dispersion_categorias_coco.png",
    },
    "boxplot": {
        "titulo": "Boxplot de área",
        "subtitulo": "Comparación del área normalizada en las 10 categorías más frecuentes",
        "constructor": boxplot_areas,
        "archivo": "boxplot_areas_coco.png",
    },
}


class VentanaPrincipal:
    """Coordina la barra lateral, las vistas y la carga de datos."""

    def __init__(self) -> None:
        self.raiz = tk.Tk()
        self.raiz.withdraw()
        self.raiz.title("COCO 2017 · Explorador de visualizaciones")
        self.raiz.configure(bg=PALETA["fondo"])
        self.raiz.minsize(1060, 700)
        configurar_estilos(self.raiz)

        self._df = None
        self._ruta_datos = ""
        self._resumen = {}
        self._clave_actual = ""
        self._cola: queue.Queue = queue.Queue()
        self._vistas: dict[str, tk.Frame] = {}
        self._filtros: dict[str, dict] = {}
        self._panel_filtros: PanelFiltros | None = None

        self._construir_interfaz()
        self._centrar(1280, 840)
        self.raiz.deiconify()
        self.raiz.protocol("WM_DELETE_WINDOW", self._cerrar)
        self._iniciar_carga()

    # ------------------------------------------------------------------
    # Construccion de la interfaz
    # ------------------------------------------------------------------
    def _construir_interfaz(self) -> None:
        self._barra_lateral = BarraLateral(
            self.raiz,
            al_seleccionar=self._seleccionar,
            al_exportar_csv=self._exportar_csv,
            al_salir=self._cerrar,
        )
        self._barra_lateral.pack(side="left", fill="y")

        contenido = tk.Frame(self.raiz, bg=PALETA["fondo"])
        contenido.pack(side="left", fill="both", expand=True)

        encabezado = tk.Frame(contenido, bg=PALETA["fondo"])
        encabezado.pack(fill="x", padx=26, pady=(22, 12))

        bloque_titulo = tk.Frame(encabezado, bg=PALETA["fondo"])
        bloque_titulo.pack(side="left", fill="x", expand=True)
        self._lbl_titulo = tk.Label(
            bloque_titulo,
            text="Preparando el explorador",
            bg=PALETA["fondo"],
            fg=PALETA["texto"],
            font=tipografia(20, "bold"),
            anchor="w",
        )
        self._lbl_titulo.pack(anchor="w")
        self._lbl_subtitulo = tk.Label(
            bloque_titulo,
            text="Leyendo el conjunto de validación de COCO 2017",
            bg=PALETA["fondo"],
            fg=PALETA["texto_tenue"],
            font=tipografia(9),
            anchor="w",
        )
        self._lbl_subtitulo.pack(anchor="w", pady=(4, 0))

        self._btn_guardar = ttk.Button(
            encabezado,
            text="Guardar PNG",
            style="Secundario.TButton",
            command=self._guardar_png,
            state="disabled",
        )
        self._btn_guardar.pack(side="right")

        self._contenedor = tk.Frame(contenido, bg=PALETA["fondo"])
        self._contenedor.pack(fill="both", expand=True, padx=26)
        self._contenedor.grid_rowconfigure(0, weight=1)
        self._contenedor.grid_columnconfigure(0, weight=1)

        barra_estado = tk.Frame(contenido, bg=PALETA["fondo"], height=38)
        barra_estado.pack(fill="x", padx=26, pady=(6, 0))
        barra_estado.pack_propagate(False)
        self._punto_estado = tk.Label(
            barra_estado,
            text="●",
            bg=PALETA["fondo"],
            fg=PALETA["aviso"],
            font=tipografia(8),
        )
        self._punto_estado.pack(side="left")
        self._lbl_estado = tk.Label(
            barra_estado,
            text="Iniciando...",
            bg=PALETA["fondo"],
            fg=PALETA["texto_tenue"],
            font=tipografia(9),
            anchor="w",
        )
        self._lbl_estado.pack(side="left", padx=(6, 0))

        tk.Label(
            contenido,
            text="Fuente: COCO val2017 · 5,000 imágenes · 80 categorías",
            bg=PALETA["fondo"],
            fg="#94A3B8",
            font=tipografia(8),
            anchor="e",
        ).pack(fill="x", padx=26, pady=(0, 10))

    def _centrar(self, ancho: int, alto: int) -> None:
        self.raiz.update_idletasks()
        x = max(0, (self.raiz.winfo_screenwidth() - ancho) // 2)
        y = max(0, (self.raiz.winfo_screenheight() - alto) // 2 - 24)
        self.raiz.geometry(f"{ancho}x{alto}+{x}+{y}")

    # ------------------------------------------------------------------
    # Carga de datos en segundo plano
    # ------------------------------------------------------------------
    def _iniciar_carga(self) -> None:
        self._lbl_titulo.configure(text="Preparando el explorador")
        self._lbl_subtitulo.configure(
            text="Leyendo el conjunto de validación de COCO 2017"
        )
        self._btn_guardar.state(["disabled"])
        self._mostrar_vista("carga")
        self._estado("Leyendo las anotaciones de COCO 2017...", "aviso")

        hilo = threading.Thread(target=self._cargar_en_hilo, daemon=True)
        hilo.start()
        self.raiz.after(120, self._revisar_cola)

    def _cargar_en_hilo(self) -> None:
        try:
            df = cargar_datos()
            self._cola.put(("ok", df, None))
        except Exception as error:  # se informa en la interfaz
            self._cola.put(("error", None, error))

    def _revisar_cola(self) -> None:
        try:
            estado, df, error = self._cola.get_nowait()
        except queue.Empty:
            self.raiz.after(120, self._revisar_cola)
            return

        if estado == "error":
            self._detener_carga()
            self._mostrar_vista("error", mensaje=str(error))
            self._estado("No se pudieron cargar los datos.", "error")
            return

        self._df = df
        self._ruta_datos = str(buscar_anotaciones())
        self._resumen = resumen_dataset(df)
        self._al_terminar_carga()

    def _detener_carga(self) -> None:
        vista = self._vistas.pop("carga", None)
        if vista is not None:
            vista.barra.stop()
            vista.destroy()

    def _al_terminar_carga(self) -> None:
        self._detener_carga()
        resumen = self._resumen
        self._barra_lateral.actualizar_resumen(resumen)
        self._filtros = {
            clave: {"categoria": TODAS_LAS_CATEGORIAS, "percentil": 0}
            for clave in ("dispersion", "categorias")
        }

        vista_info = VistaInfo(
            self._contenedor,
            self._df,
            self._ruta_datos,
            resumen,
        )
        vista_info.grid(row=0, column=0, sticky="nsew")
        self._vistas["info"] = vista_info

        self._barra_lateral.habilitar_datos(True)

        self._seleccionar("histograma")

    # ------------------------------------------------------------------
    # Navegacion y acciones
    # ------------------------------------------------------------------
    def _mostrar_vista(self, nombre: str, **kwargs) -> None:
        if nombre == "carga":
            vista = self._vistas.get("carga")
            if vista is None:
                vista = VistaCarga(self._contenedor)
                vista.grid(row=0, column=0, sticky="nsew")
                self._vistas["carga"] = vista
        elif nombre == "error":
            anterior = self._vistas.pop("error", None)
            if anterior is not None:
                anterior.destroy()
            vista = VistaError(
                self._contenedor,
                kwargs.get("mensaje", ""),
                self._reiniciar_carga,
            )
            vista.grid(row=0, column=0, sticky="nsew")
            self._vistas["error"] = vista
        else:
            vista = self._vistas[nombre]
        vista.tkraise()

    def _reiniciar_carga(self) -> None:
        error = self._vistas.pop("error", None)
        if error is not None:
            error.destroy()
        self._filtros = {}
        self._panel_filtros = None
        self._iniciar_carga()

    def _seleccionar(self, clave: str) -> None:
        if self._df is None:
            return

        if clave == "info":
            self._marcar_boton_activo("info")
            self._lbl_titulo.configure(text="Información del dataset")
            self._lbl_subtitulo.configure(
                text="Resumen general y categorías con más anotaciones"
            )
            self._btn_guardar.state(["disabled"])
            self._mostrar_vista("info")
            self._estado("Resumen del conjunto de validación de COCO 2017.", "ok")
            return

        if clave not in VISTAS:
            return

        if self._panel_filtros is not None:
            self._panel_filtros.cancelar()

        definicion = VISTAS[clave]
        self._marcar_boton_activo(clave)
        self._lbl_titulo.configure(text=definicion["titulo"])
        self._lbl_subtitulo.configure(text=definicion["subtitulo"])
        self._btn_guardar.state(["!disabled"])
        self._clave_actual = clave

        vista = self._vistas.get("grafica")
        if vista is None:
            vista = VistaGrafica(self._contenedor)
            vista.grid(row=0, column=0, sticky="nsew")
            self._vistas["grafica"] = vista

        self._configurar_controles(clave, vista)
        self._dibujar_grafica(clave)
        vista.tkraise()

    def _configurar_controles(self, clave: str, vista: VistaGrafica) -> None:
        vista.limpiar_controles()
        self._panel_filtros = None

        if clave not in self._filtros:
            return

        estado = self._filtros[clave]
        categorias = self._df["category"].dropna().unique().tolist()
        panel = PanelFiltros(
            vista.usar_controles(),
            categorias,
            estado["categoria"],
            estado["percentil"],
            lambda categoria, percentil: self._aplicar_filtro(
                clave, categoria, percentil
            ),
        )
        panel.pack(fill="x")
        self._panel_filtros = panel

    def _aplicar_filtro(
        self, clave: str, categoria: str, percentil: int
    ) -> None:
        estado = self._filtros.get(clave)
        if estado is None:
            return
        estado["categoria"] = categoria
        estado["percentil"] = percentil
        self._dibujar_grafica(clave)

    def _datos_filtrados(self, clave: str) -> tuple:
        estado = self._filtros.get(clave)
        if estado is None:
            return self._df, ""

        datos = self._df
        contexto = []
        if estado["categoria"] != TODAS_LAS_CATEGORIAS:
            datos = datos[datos["category"] == estado["categoria"]]
            contexto.append(estado["categoria"])

        if estado["percentil"] > 0 and not datos.empty:
            umbral = float(
                datos["area_norm"].quantile(estado["percentil"] / 100)
            )
            datos = datos[datos["area_norm"] >= umbral]
            contexto.append(f"área ≥ P{estado['percentil']}")

        return datos.copy(), " · ".join(contexto)

    def _dibujar_grafica(self, clave: str) -> None:
        vista = self._vistas.get("grafica")
        if vista is None or self._df is None or clave not in VISTAS:
            return

        datos, contexto = self._datos_filtrados(clave)
        if datos.empty:
            self._estado("El filtro no deja anotaciones para mostrar.", "aviso")
            return

        definicion = VISTAS[clave]
        subtitulo = definicion["subtitulo"]
        if contexto:
            subtitulo = f"{subtitulo} · {contexto}"
        self._lbl_subtitulo.configure(text=subtitulo)

        self._estado("Generando la gráfica...", "aviso")
        self.raiz.update_idletasks()

        try:
            figura = definicion["constructor"](datos, contexto=contexto)
            vista.mostrar(figura)
            if self._panel_filtros is not None:
                self._panel_filtros.actualizar_conteo(
                    f"{len(datos):,} puntos"
                )
            self._estado(
                f"{definicion['titulo']} · {len(datos):,} anotaciones", "ok"
            )
        except Exception as error:
            self._estado(f"No se pudo generar la gráfica: {error}", "error")
            messagebox.showerror(
                "Error al generar la gráfica",
                f"No se pudo generar la visualización:\n\n{error}",
                parent=self.raiz,
            )

    def _marcar_boton_activo(self, clave: str) -> None:
        self._barra_lateral.marcar_activo(clave)

    def _exportar_csv(self) -> None:
        if self._df is None:
            return
        try:
            destino = exportar_csv(self._df)
            self._estado(f"CSV exportado: {destino.name}", "ok")
            messagebox.showinfo(
                "CSV exportado",
                "Archivo listo para Tableau Public:\n\n"
                f"{destino}\n\n"
                f"Registros: {len(self._df):,}",
                parent=self.raiz,
            )
        except Exception as error:
            self._estado(f"No se pudo exportar el CSV: {error}", "error")
            messagebox.showerror(
                "Error al exportar", str(error), parent=self.raiz
            )

    def _guardar_png(self) -> None:
        vista = self._vistas.get("grafica")
        if vista is None or vista.figura is None:
            return

        definicion = VISTAS.get(self._clave_actual, {})
        preparar_salidas()
        destino = filedialog.asksaveasfilename(
            parent=self.raiz,
            title="Guardar gráfica como PNG",
            initialdir=str(preparar_salidas()),
            initialfile=definicion.get("archivo", "grafica_coco.png"),
            defaultextension=".png",
            filetypes=[("Imagen PNG", "*.png")],
        )
        if not destino:
            return

        try:
            ruta = guardar_imagen(vista.figura, destino)
            self._estado(f"Imagen guardada: {ruta.name}", "ok")
        except Exception as error:
            self._estado(f"No se pudo guardar la imagen: {error}", "error")
            messagebox.showerror(
                "Error al guardar", str(error), parent=self.raiz
            )

    def _estado(self, mensaje: str, tono: str = "ok") -> None:
        colores = {
            "ok": PALETA["exito"],
            "aviso": PALETA["aviso"],
            "error": PALETA["error"],
        }
        self._punto_estado.configure(fg=colores.get(tono, PALETA["texto_tenue"]))
        self._lbl_estado.configure(text=mensaje)

    def _cerrar(self) -> None:
        if self._panel_filtros is not None:
            self._panel_filtros.cancelar()
        self.raiz.destroy()

    def ejecutar(self) -> None:
        self.raiz.mainloop()

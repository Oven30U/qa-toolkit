"""Ventana principal: pestana Conexion + una pestana por modulo + panel de logs."""

from __future__ import annotations

import queue
import tkinter as tk
from tkinter import ttk

from qa_toolkit import APP_NAME, __version__
from qa_toolkit.core.config import Settings
from qa_toolkit.core.logging_setup import setup_logging
from qa_toolkit.modules.registry import MODULES
from qa_toolkit.ui.connection_view import ConnectionView
from qa_toolkit.ui.context import AppContext
from qa_toolkit.ui.widgets import LogPanel


def _estilos(root: tk.Tk) -> None:
    st = ttk.Style(root)
    if "clam" in st.theme_names():
        st.theme_use("clam")
    st.configure("Title.TLabel", font=("Segoe UI", 14, "bold"))
    st.configure("Section.TLabel", font=("Segoe UI", 10, "bold"))
    st.configure("Muted.TLabel", foreground="#6B7280")
    st.configure("Accent.TButton", font=("Segoe UI", 9, "bold"), foreground="white", background="#2563EB")
    st.map("Accent.TButton", background=[("active", "#1D4ED8"), ("disabled", "#9CA3AF")])


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{__version__}")
        self.geometry("980x760")
        self.minsize(820, 620)
        _estilos(self)

        cola_logs: queue.Queue = queue.Queue()
        logger = setup_logging(cola_logs)
        self.ctx = AppContext(self, Settings.from_env(), logger)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=(10, 4))
        notebook.add(ConnectionView(notebook, self.ctx), text="Conexión")
        for spec in MODULES:
            vista = spec.load_view_class()(notebook, self.ctx)
            notebook.add(vista, text=spec.title)

        LogPanel(self, cola_logs).pack(fill="both", expand=False, padx=10, pady=4)

        barra = ttk.Frame(self)
        barra.pack(fill="x", padx=10, pady=(0, 8))
        self.estado = ttk.Label(barra, text="Listo", style="Muted.TLabel")
        self.estado.pack(side="left")
        self.cancelar = ttk.Button(barra, text="Cancelar tarea", command=self.ctx.cancel, state="disabled")
        self.cancelar.pack(side="right")
        self.progreso = ttk.Progressbar(barra, mode="indeterminate", length=160)
        self.progreso.pack(side="right", padx=8)
        self.ctx.on_busy_change = self._on_busy

        logger.info("%s iniciado. Configurá la pestaña Conexión y elegí una herramienta.", APP_NAME)

    def _on_busy(self, busy: bool):
        self.estado.configure(text="Ejecutando…" if busy else "Listo")
        self.cancelar.configure(state="normal" if busy else "disabled")
        if busy:
            self.progreso.start(12)
        else:
            self.progreso.stop()


def main() -> None:
    App().mainloop()

"""Widgets reutilizables."""

from __future__ import annotations

import logging
import logging.handlers
import queue
import tkinter as tk
from tkinter import filedialog, ttk
from tkinter.scrolledtext import ScrolledText


class LogPanel(ttk.Frame):
    """Muestra los logs del sistema en vivo (consume la cola del QueueHandler)."""

    def __init__(self, parent, log_queue: "queue.Queue[logging.LogRecord]"):
        super().__init__(parent)
        self._cola = log_queue
        barra = ttk.Frame(self)
        barra.pack(fill="x")
        ttk.Label(barra, text="Registro de actividad", style="Section.TLabel").pack(side="left")
        ttk.Button(barra, text="Limpiar", command=self.limpiar).pack(side="right")
        ttk.Button(barra, text="Guardar…", command=self.guardar).pack(side="right", padx=4)
        self.texto = ScrolledText(
            self,
            height=11,
            state="disabled",
            wrap="word",
            font=("Consolas", 9),
            background="#101820",
            foreground="#E6EDF3",
        )
        self.texto.pack(fill="both", expand=True, pady=(4, 0))
        for nivel, color in (
            ("INFO", "#E6EDF3"),
            ("WARNING", "#F2CC60"),
            ("ERROR", "#FF7B72"),
            ("CRITICAL", "#FF7B72"),
        ):
            self.texto.tag_configure(nivel, foreground=color)
        self._fmt = logging.Formatter("%(asctime)s  %(message)s", "%H:%M:%S")
        self.after(100, self._drenar)

    def _drenar(self):
        try:
            while True:
                rec = self._cola.get_nowait()
                self._escribir(self._fmt.format(rec) + "\n", rec.levelname)
        except queue.Empty:
            pass
        self.after(100, self._drenar)

    def _escribir(self, linea: str, nivel: str):
        self.texto.configure(state="normal")
        self.texto.insert("end", linea, nivel)
        self.texto.see("end")
        self.texto.configure(state="disabled")

    def limpiar(self):
        self.texto.configure(state="normal")
        self.texto.delete("1.0", "end")
        self.texto.configure(state="disabled")

    def guardar(self):
        ruta = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Texto", "*.txt")])
        if ruta:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(self.texto.get("1.0", "end"))


def fila_campo(
    parent,
    fila: int,
    etiqueta: str,
    variable: tk.Variable,
    *,
    ancho: int = 60,
    show: str | None = None,
    examinar=None,
) -> ttk.Entry:
    """Etiqueta + Entry (+ boton 'Examinar…' opcional) en una grilla de 3 columnas."""
    ttk.Label(parent, text=etiqueta).grid(row=fila, column=0, sticky="w", padx=(0, 10), pady=4)
    entry = ttk.Entry(parent, textvariable=variable, width=ancho, show=show or "")
    entry.grid(row=fila, column=1, sticky="ew", pady=4)
    if examinar:
        ttk.Button(parent, text="Examinar…", command=examinar).grid(row=fila, column=2, padx=(6, 0))
    return entry


def elegir_archivo(variable: tk.Variable, tipos=(("Excel", "*.xlsx"),), guardar: bool = False):
    def _cmd():
        f = filedialog.asksaveasfilename if guardar else filedialog.askopenfilename
        kw = {"defaultextension": ".xlsx"} if guardar else {}
        ruta = f(filetypes=list(tipos), **kw)
        if ruta:
            variable.set(ruta)

    return _cmd

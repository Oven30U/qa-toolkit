"""Estado compartido de la GUI: variables de configuracion, PAT, logger y ejecutor de tareas."""

from __future__ import annotations

import logging
import queue
import tkinter as tk
from dataclasses import fields
from tkinter import messagebox

from qa_toolkit.core.azdo import AzureDevOpsClient
from qa_toolkit.core.config import Settings, pat_desde_entorno
from qa_toolkit.core.errors import AzdoError, CancelledError, ConfigError, QAToolkitError
from qa_toolkit.core.ssl_utils import usar_certificados_del_sistema
from qa_toolkit.core.tasks import CancelToken, run_in_thread

_ENTEROS = {"plan_id", "suite_id"}
_BOOLEANOS = {"use_system_certs", "verify_ssl", "solo_primer_caso", "incluir_inactivos"}


class AppContext:
    def __init__(self, root: tk.Tk, settings: Settings, logger: logging.Logger):
        self.root = root
        self.log = logger
        self.vars: dict[str, tk.Variable] = {}
        for f in fields(Settings):
            valor = getattr(settings, f.name)
            if f.name in _BOOLEANOS:
                self.vars[f.name] = tk.BooleanVar(value=valor)
            else:
                self.vars[f.name] = tk.StringVar(value="" if valor in (0, None) else str(valor))
        self.pat = tk.StringVar(value=pat_desde_entorno())  # solo en memoria
        self.action_buttons: list = []  # se deshabilitan mientras corre una tarea
        self._busy = False
        self._cola: queue.Queue = queue.Queue()
        self._token: CancelToken | None = None
        self.on_busy_change = lambda busy: None
        self.root.after(100, self._poll)

    # ------------------------------------------------------------ settings
    def read_settings(self) -> Settings:
        datos = {}
        for nombre, var in self.vars.items():
            valor = var.get()
            if nombre in _ENTEROS:
                try:
                    valor = int(str(valor).strip() or 0)
                except ValueError as e:
                    raise ConfigError(f"'{nombre}' debe ser un número entero.") from e
            elif nombre not in _BOOLEANOS:
                valor = str(valor).strip()
            datos[nombre] = valor
        datos["azdo_url"] = datos["azdo_url"].rstrip("/")
        return Settings(**datos)

    def build_client(self, settings: Settings, api_version: str | None = None) -> AzureDevOpsClient:
        if settings.use_system_certs:
            usar_certificados_del_sistema()
        return AzureDevOpsClient(
            settings.azdo_url,
            settings.project,
            self.pat.get().strip(),
            api_version or settings.api_version,
            verify_ssl=settings.verify_ssl,
        )

    # ------------------------------------------------------------- tareas
    def register_button(self, boton):
        self.action_buttons.append(boton)
        return boton

    @property
    def busy(self) -> bool:
        return self._busy

    def cancel(self):
        if self._token:
            self._token.cancel()
            self.log.warning("Cancelando… se detiene al terminar el paso actual.")

    def _set_busy(self, busy: bool):
        self._busy = busy
        for b in self.action_buttons:
            b.configure(state="disabled" if busy else "normal")
        self.on_busy_change(busy)

    def run_task(self, nombre: str, trabajo, on_success=None):
        """Ejecuta `trabajo(token)` en segundo plano. `on_success(resultado)` corre en el hilo de la GUI."""
        if self._busy:
            messagebox.showinfo("Tarea en curso", "Hay otra tarea ejecutándose. Esperá a que termine.")
            return
        self._token = CancelToken()
        self._set_busy(True)
        self.log.info("▶ %s", nombre)

        def _done(resultado, error):
            self._cola.put((nombre, resultado, error, on_success))

        run_in_thread(trabajo, _done, self._token)

    def _poll(self):
        try:
            while True:
                nombre, resultado, error, on_success = self._cola.get_nowait()
                self._set_busy(False)
                self._token = None
                self._terminar(nombre, resultado, error, on_success)
        except queue.Empty:
            pass
        self.root.after(100, self._poll)

    def _terminar(self, nombre, resultado, error, on_success):
        if error is None:
            self.log.info("✔ %s: terminado", nombre)
            if on_success:
                on_success(resultado)
        elif isinstance(error, CancelledError):
            self.log.warning("■ %s: cancelado", nombre)
        elif isinstance(error, AzdoError):
            self.log.error("✖ %s\n%s", nombre, error.detalle())
            messagebox.showerror(nombre, str(error))
        elif isinstance(error, QAToolkitError):
            self.log.error("✖ %s: %s", nombre, error)
            messagebox.showerror(nombre, str(error))
        else:
            self.log.error("✖ %s: error inesperado", nombre, exc_info=error)
            messagebox.showerror(nombre, f"Error inesperado: {error}\nVer logs/qa_toolkit.log")

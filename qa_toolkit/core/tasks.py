"""Ejecucion de tareas largas en segundo plano, sin congelar la GUI (sin tkinter)."""

from __future__ import annotations

import threading
from typing import Callable

from qa_toolkit.core.errors import CancelledError


class CancelToken:
    """Los servicios llaman a `check()` entre pasos para permitir cancelar."""

    def __init__(self):
        self._evento = threading.Event()

    def cancel(self):
        self._evento.set()

    @property
    def cancelled(self) -> bool:
        return self._evento.is_set()

    def check(self):
        if self._evento.is_set():
            raise CancelledError("Tarea cancelada por el usuario.")


def run_in_thread(
    trabajo: Callable[[CancelToken], object],
    on_done: Callable[[object, BaseException | None], None],
    token: CancelToken,
) -> threading.Thread:
    """Corre `trabajo(token)` en un hilo y llama `on_done(resultado, error)` al terminar.

    OJO: `on_done` se invoca en el hilo de trabajo; la GUI debe reenviarlo a su hilo
    principal (ver `ui/runner.py`).
    """

    def _target():
        try:
            resultado, error = trabajo(token), None
        except BaseException as e:  # noqa: BLE001 - se reenvia a la GUI
            resultado, error = None, e
        on_done(resultado, error)

    hilo = threading.Thread(target=_target, daemon=True)
    hilo.start()
    return hilo

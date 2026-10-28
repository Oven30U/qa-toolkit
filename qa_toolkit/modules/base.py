"""Contrato de un modulo: metadatos + ruta a su vista Tkinter (carga diferida)."""

from __future__ import annotations

import importlib
from dataclasses import dataclass


@dataclass(frozen=True)
class ModuleSpec:
    id: str
    title: str  # texto de la pestana
    description: str
    view_path: str  # "paquete.modulo:ClaseVista"

    def load_view_class(self):
        modulo, clase = self.view_path.split(":")
        return getattr(importlib.import_module(modulo), clase)

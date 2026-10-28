"""Registro de modulos. Para sumar una herramienta nueva, agregala a MODULES."""

from qa_toolkit.modules.base import ModuleSpec
from qa_toolkit.modules.testcase_importer import SPEC as IMPORTER
from qa_toolkit.modules.testplan_reports import SPEC as REPORTS

MODULES: list[ModuleSpec] = [
    IMPORTER,
    REPORTS,
]

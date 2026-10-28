import logging
from types import SimpleNamespace

import pytest

from qa_toolkit.core.config import Settings
from qa_toolkit.core.errors import AzdoError, ConfigError
from qa_toolkit.core.tasks import CancelToken
from qa_toolkit.modules.testcase_importer.excel_reader import generar_plantilla
from qa_toolkit.modules.testcase_importer.service import ImportadorTestCases


class FakeClient:
    def __init__(self, en_suite=None, falla_agregar=False):
        self.en_suite, self.falla_agregar, self.llamadas = en_suite or [], falla_agregar, []

    def validar_conexion(self):
        return {"name": "P"}

    def obtener_work_item(self, wid):
        tipo = {1: "Test Plan", 2: "Test Suite"}.get(wid, "Test Case")
        return {"fields": {"System.WorkItemType": tipo, "System.Title": "t"}}

    def get_json(self, path, **kw):
        return {"value": self.en_suite}

    def request(self, method, path, **kw):
        self.llamadas.append((method, path))
        if "testcases/" in path and self.falla_agregar:
            raise AzdoError("boom")
        return SimpleNamespace(json=lambda: {"id": 500})


def _settings(tmp_path):
    ruta = tmp_path / "c.xlsx"
    generar_plantilla(str(ruta))
    return Settings(azdo_url="u", project="p", plan_id=1, suite_id=2, excel_file=str(ruta))


def test_crea_y_agrega(tmp_path):
    c = FakeClient()
    r = ImportadorTestCases(c, logging.getLogger("t")).ejecutar(_settings(tmp_path), CancelToken())
    assert (r.creados, r.agregados, r.errores) == (1, 1, 0)


def test_reutiliza_si_ya_esta_en_suite(tmp_path):
    existente = [{"testCase": {"workItem": {"id": 77, "name": "[CP-001] algo"}}}]
    c = FakeClient(en_suite=existente)
    r = ImportadorTestCases(c, logging.getLogger("t")).ejecutar(_settings(tmp_path), CancelToken())
    assert (r.creados, r.reutilizados, r.agregados) == (0, 1, 1)
    assert not any(m == "POST" and "workitems" in p for m, p in c.llamadas)


def test_error_al_agregar_se_cuenta(tmp_path):
    c = FakeClient(falla_agregar=True)
    r = ImportadorTestCases(c, logging.getLogger("t")).ejecutar(_settings(tmp_path), CancelToken())
    assert r.errores == 1 and r.detalle[0].resultado == "ERROR"


def test_config_incompleta():
    with pytest.raises(ConfigError):
        ImportadorTestCases.validar_config(Settings())


def test_cancelacion(tmp_path):
    from qa_toolkit.core.errors import CancelledError

    t = CancelToken()
    t.cancel()
    with pytest.raises(CancelledError):
        ImportadorTestCases(FakeClient(), logging.getLogger("t")).ejecutar(_settings(tmp_path), t)

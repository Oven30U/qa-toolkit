import logging

import pandas as pd

from qa_toolkit.core.config import Settings
from qa_toolkit.core.tasks import CancelToken
from qa_toolkit.modules.testplan_reports.service import (
    ReporteTestPlans,
    armar_resumen,
    seleccionar_planes,
)

PLANES = [
    {"id": 1, "name": "Plan_Regresion_1", "state": "Active"},
    {"id": 2, "name": "Otro", "state": "Inactive"},
]


def test_filtros():
    assert [p["id"] for p in seleccionar_planes(PLANES, "", False)] == [1]
    assert [p["id"] for p in seleccionar_planes(PLANES, "", True)] == [1, 2]
    assert [p["id"] for p in seleccionar_planes(PLANES, "regresion_1", True)] == [1]


class FakeClient:
    api_version = "4.1"

    def get_paged(self, path, **kw):
        if path.endswith("/plans"):
            return PLANES
        if path.endswith("/suites"):
            return [{"id": 10, "name": "S"}]
        return [
            {"testCase": {"id": "1", "name": "a"}, "outcome": "Passed", "state": "Completed"},
            {"testCase": {"id": "2", "name": "b"}, "outcome": "Failed", "state": "Completed"},
        ]


def test_genera_excel(tmp_path):
    s = Settings(azdo_url="u", project="p", reports_output_file=str(tmp_path / "o.xlsx"))
    r = ReporteTestPlans(FakeClient(), logging.getLogger("t")).ejecutar(s, CancelToken())
    assert r.filas == 2 and r.planes == 1
    hojas = pd.read_excel(r.archivo, sheet_name=None)
    assert set(hojas) == {"Detalle", "Resumen"}
    assert list(hojas["Detalle"].columns)[:3] == ["PlanId", "Plan", "EstadoPlan"]


def test_resumen_cuenta_por_resultado():
    df = pd.DataFrame({"Plan": ["A", "A"], "Resultado": ["Passed", "Failed"], "TestCaseId": [1, 2]})
    res = armar_resumen(df)
    assert res.loc[0, "Passed"] == 1 and res.loc[0, "Failed"] == 1

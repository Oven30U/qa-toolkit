"""Descarga de resultados de Test Plans -> Excel (Detalle + Resumen) para Power BI."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from qa_toolkit.core.azdo import AzureDevOpsClient
from qa_toolkit.core.config import Settings
from qa_toolkit.core.errors import ConfigError, QAToolkitError
from qa_toolkit.core.tasks import CancelToken


@dataclass
class ResultadoReporte:
    archivo: str
    filas: int
    planes: int
    resumen: pd.DataFrame


def _parse_filtros(texto: str) -> list[str]:
    return [f.strip().lower() for f in texto.split(",") if f.strip()]


def seleccionar_planes(planes: list[dict], filtro: str, incluir_inactivos: bool) -> list[dict]:
    filtros = _parse_filtros(filtro)
    if filtros:
        planes = [p for p in planes if any(f in p["name"].lower() for f in filtros)]
    if not incluir_inactivos:
        planes = [p for p in planes if str(p.get("state", "")).lower() != "inactive"]
    return planes


def punto_a_fila(plan: dict, suite: dict, pt: dict) -> dict:
    return {
        "PlanId": plan["id"],
        "Plan": plan["name"],
        "EstadoPlan": plan.get("state", ""),
        "SuiteId": suite["id"],
        "Suite": suite["name"],
        "TestCaseId": (pt.get("testCase") or {}).get("id"),
        "TestCase": (pt.get("testCase") or {}).get("name"),
        "Resultado": pt.get("outcome"),
        "Estado": pt.get("state"),
        "Tester": (pt.get("tester") or {}).get("displayName"),
        "Configuracion": (pt.get("configuration") or {}).get("name"),
        "UltimaActualizacion": pt.get("lastUpdatedDate"),
    }


def armar_resumen(df: pd.DataFrame) -> pd.DataFrame:
    return df.pivot_table(
        index="Plan", columns="Resultado", values="TestCaseId", aggfunc="count", fill_value=0
    ).reset_index()


class ReporteTestPlans:
    def __init__(self, client: AzureDevOpsClient, logger: logging.Logger):
        self.client = client
        self.log = logger

    def ejecutar(self, s: Settings, cancel: CancelToken) -> ResultadoReporte:
        if not s.reports_output_file:
            raise ConfigError("Indicá el archivo Excel de salida.")
        self.log.info(
            "Consultando Test Plans en %s/%s (api %s)…", s.azdo_url, s.project, self.client.api_version
        )
        planes = self.client.get_paged("/_apis/test/plans", operation="listar Test Plans")
        self.log.info("Planes encontrados: %d", len(planes))
        planes = seleccionar_planes(planes, s.filtro_planes, s.incluir_inactivos)
        self.log.info("Planes a procesar: %s", [p["name"] for p in planes])

        filas = []
        for plan in planes:
            cancel.check()
            suites = self.client.get_paged(
                f"/_apis/test/plans/{plan['id']}/suites", operation=f"listar suites de {plan['name']}"
            )
            self.log.info("- %s: %d suites", plan["name"], len(suites))
            for suite in suites:
                cancel.check()
                puntos = self.client.get_paged(
                    f"/_apis/test/plans/{plan['id']}/suites/{suite['id']}/points",
                    operation=f"listar test points de la suite {suite['name']}",
                )
                filas.extend(punto_a_fila(plan, suite, pt) for pt in puntos)

        df = pd.DataFrame(filas)
        if df.empty:
            raise QAToolkitError(
                "No se encontraron test points. Revisá el filtro de planes o los permisos del PAT."
            )
        resumen = armar_resumen(df)

        destino = Path(s.reports_output_file)
        destino.parent.mkdir(parents=True, exist_ok=True)
        try:
            with pd.ExcelWriter(destino, engine="openpyxl") as xl:
                df.to_excel(xl, sheet_name="Detalle", index=False)
                resumen.to_excel(xl, sheet_name="Resumen", index=False)
        except PermissionError as e:
            raise QAToolkitError(
                f"No se pudo escribir {destino}. ¿Está abierto en Excel o Power BI? Cerralo y reintentá."
            ) from e
        self.log.info("Listo: %d filas guardadas en %s", len(df), destino)
        return ResultadoReporte(str(destino), len(df), len(planes), resumen)

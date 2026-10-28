"""Logica del importador: sin tkinter, sin prints. Reporta via logger y devuelve un resumen."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from html import escape

from qa_toolkit.core.azdo import AzureDevOpsClient
from qa_toolkit.core.config import Settings
from qa_toolkit.core.errors import AzdoError, ConfigError
from qa_toolkit.core.tasks import CancelToken
from qa_toolkit.modules.testcase_importer.excel_reader import (
    COLUMNAS_REQUERIDAS,
    cargar_excel,
    construir_steps_xml,
    limpiar_valor,
)


@dataclass
class ResultadoCaso:
    id_caso: str
    work_item_id: int | str
    resultado: str  # "OK" | "ERROR"
    detalle: str


@dataclass
class ResumenImportacion:
    creados: int = 0
    reutilizados: int = 0
    agregados: int = 0
    errores: int = 0
    detalle: list[ResultadoCaso] = field(default_factory=list)


class ImportadorTestCases:
    def __init__(self, client: AzureDevOpsClient, logger: logging.Logger):
        self.client = client
        self.log = logger

    # -------------------------------------------------------- validaciones
    @staticmethod
    def validar_config(s: Settings) -> None:
        faltan = [
            n
            for n, v in (
                ("URL de Azure DevOps", s.azdo_url),
                ("Proyecto", s.project),
                ("Plan ID", s.plan_id),
                ("Suite ID", s.suite_id),
                ("Archivo Excel", s.excel_file),
            )
            if not v
        ]
        if faltan:
            raise ConfigError("Faltan datos de configuración:\n" + "\n".join(f"- {f}" for f in faltan))

    def _validar_tipo(self, wi_id: int, esperado: str, etiqueta: str) -> None:
        wi = self.client.obtener_work_item(wi_id)
        campos = wi.get("fields", {})
        tipo = str(campos.get("System.WorkItemType", "")).strip()
        titulo = str(campos.get("System.Title", "")).strip()
        self.log.info("%s encontrado: ID %s | Tipo: %s | Título: %s", etiqueta, wi_id, tipo, titulo)
        if tipo.casefold() != esperado:
            raise AzdoError(f"El Work Item {wi_id} no es de tipo {etiqueta} (es '{tipo}').")

    def validar_plan_y_suite(self, plan_id: int, suite_id: int) -> None:
        self._validar_tipo(plan_id, "test plan", "Test Plan")
        self._validar_tipo(suite_id, "test suite", "Test Suite")

    # ------------------------------------------------------ API especifica
    def test_cases_de_la_suite(self, plan_id: int, suite_id: int) -> dict[str, int]:
        """{ID caso de prueba: Work Item ID} de lo que YA esta en esta suite (y solo en esta)."""
        data = self.client.get_json(
            f"/_apis/test/Plans/{plan_id}/suites/{suite_id}/testcases",
            operation="consultar los Test Cases ya agregados a la suite destino",
        )
        encontrados = {}
        for item in data.get("value", []):
            wi = (item.get("testCase") or {}).get("workItem") or {}
            m = re.match(r"^\[([^\]]+)\]", str(wi.get("name", "")))
            if wi.get("id") and m:
                encontrados[m.group(1).strip()] = int(wi["id"])
        return encontrados

    def crear_test_case(self, datos: dict, steps_xml: str) -> int:
        tc_id = datos["ID caso de prueba"]
        tags = "; ".join(v for v in (tc_id, datos["Módulo"], datos["Funcionalidad"]) if v)
        body = [
            {
                "op": "add",
                "path": "/fields/System.Title",
                "value": f"[{tc_id}] {datos['Nombre del caso de prueba']}",
            },
            {
                "op": "add",
                "path": "/fields/System.Description",
                "value": escape(datos["Descripción del caso de prueba"]),
            },
            {"op": "add", "path": "/fields/System.Tags", "value": tags},
            {"op": "add", "path": "/fields/Microsoft.VSTS.TCM.Steps", "value": steps_xml},
        ]
        r = self.client.request(
            "POST",
            "/_apis/wit/workitems/$Test%20Case",
            json=body,
            headers={"Content-Type": "application/json-patch+json"},
            operation=f"crear el Test Case {tc_id}",
        )
        return int(r.json()["id"])

    def agregar_a_suite(self, plan_id: int, suite_id: int, wi_id: int, tc_id: str) -> None:
        self.client.request(
            "POST",
            f"/_apis/test/Plans/{plan_id}/suites/{suite_id}/testcases/{wi_id}",
            headers={"Content-Type": "application/json"},
            operation=f"agregar {tc_id} (WI {wi_id}) al Plan {plan_id}, Suite {suite_id}",
        )

    # ------------------------------------------------------------- flujo
    def ejecutar(self, s: Settings, cancel: CancelToken) -> ResumenImportacion:
        self.validar_config(s)
        self.log.info("Validando conexión y proyecto…")
        proyecto = self.client.validar_conexion()
        self.log.info("Conexión correcta. Proyecto: %s", proyecto.get("name", s.project))
        self.validar_plan_y_suite(s.plan_id, s.suite_id)

        df = cargar_excel(s.excel_file, s.excel_sheet_name, s.solo_primer_caso)
        en_suite = self.test_cases_de_la_suite(s.plan_id, s.suite_id)
        self.log.info(
            "Proyecto: %s | Plan: %s (%s) | Suite: %s | Casos a procesar: %d | Ya en la suite: %d",
            s.project,
            s.test_plan_name or "-",
            s.plan_id,
            s.suite_id,
            len(df),
            len(en_suite),
        )
        if en_suite:
            self.log.warning(
                "Hay %d casos ya presentes en la suite: se reutilizan para no duplicar.", len(en_suite)
            )

        resumen = ResumenImportacion()
        for _, fila in df.iterrows():
            cancel.check()
            datos = {c: limpiar_valor(fila[c]) for c in COLUMNAS_REQUERIDAS}
            tc_id = datos["ID caso de prueba"]
            self.log.info("Procesando %s - %s", tc_id, datos["Nombre del caso de prueba"])
            existente = en_suite.get(tc_id)
            try:
                if existente is not None:
                    self._validar_tipo(existente, "test case", "Test Case")
                    wi_id = existente
                    resumen.reutilizados += 1
                    self.log.info("REUTILIZANDO %s (WI %s)", tc_id, wi_id)
                else:
                    steps = construir_steps_xml(
                        datos["Instrucciones de ejecución"], datos["Resultado esperado"]
                    )
                    wi_id = self.crear_test_case(datos, steps)
                    resumen.creados += 1
                    self.log.info("CREADO %s (WI nuevo %s)", tc_id, wi_id)
                self.agregar_a_suite(s.plan_id, s.suite_id, wi_id, tc_id)
                resumen.agregados += 1
                resumen.detalle.append(
                    ResultadoCaso(
                        tc_id,
                        wi_id,
                        "OK",
                        "Creado y agregado"
                        if existente is None
                        else "Reutilizado (ya estaba en esta suite) y agregado",
                    )
                )
            except AzdoError as e:
                resumen.errores += 1
                self.log.error("%s: %s", tc_id, e.detalle())
                resumen.detalle.append(ResultadoCaso(tc_id, existente or "", "ERROR", str(e)))

        self.log.info(
            "FINALIZADO | creados=%d reutilizados=%d agregados=%d errores=%d",
            resumen.creados,
            resumen.reutilizados,
            resumen.agregados,
            resumen.errores,
        )
        return resumen

"""
Configuracion central de la aplicacion.

Los valores por defecto se leen de `.env` (ver `.env.example`). La GUI los
muestra en la pestana "Conexion" y los modulos, y permite guardarlos de
vuelta en `.env`.

El Personal Access Token (PAT) NUNCA se guarda en disco: vive solo en memoria
durante la sesion (se puede precargar con la variable de entorno AZDO_PAT).
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from dotenv import load_dotenv

from qa_toolkit.core.paths import ENV_FILE, OUTPUT_DIR


def _bool(valor: str, default: bool) -> bool:
    valor = (valor or "").strip().lower()
    if not valor:
        return default
    return valor in ("1", "true", "si", "sí", "yes", "y")


def _int(valor: str) -> int:
    try:
        return int((valor or "").strip())
    except ValueError:
        return 0


@dataclass
class Settings:
    # --- Conexion compartida ---
    azdo_url: str = ""
    project: str = ""
    api_version: str = "5.1"
    use_system_certs: bool = True
    verify_ssl: bool = True
    # --- Modulo: importador de Test Cases ---
    test_plan_name: str = ""
    plan_id: int = 0
    suite_id: int = 0
    excel_file: str = ""
    excel_sheet_name: str = "Casos de prueba"
    solo_primer_caso: bool = False
    # --- Modulo: reportes de Test Plans ---
    reports_api_version: str = "4.1"
    filtro_planes: str = ""  # nombres separados por coma; vacio = todos
    incluir_inactivos: bool = False
    reports_output_file: str = str(OUTPUT_DIR / "testplans_resultados.xlsx")

    @classmethod
    def from_env(cls, env_file: Path = ENV_FILE) -> "Settings":
        if env_file.exists():
            load_dotenv(env_file)
        e = os.environ.get
        d = cls()
        return cls(
            azdo_url=e("AZDO_URL", "").strip().rstrip("/"),
            project=e("PROJECT", "").strip(),
            api_version=e("API_VERSION", d.api_version).strip(),
            use_system_certs=_bool(e("USE_SYSTEM_CERTS", ""), d.use_system_certs),
            verify_ssl=_bool(e("VERIFY_SSL", ""), d.verify_ssl),
            test_plan_name=e("TEST_PLAN_NAME", "").strip(),
            plan_id=_int(e("PLAN_ID", "")),
            suite_id=_int(e("SUITE_ID", "")),
            excel_file=e("EXCEL_FILE", "").strip(),
            excel_sheet_name=e("EXCEL_SHEET_NAME", d.excel_sheet_name).strip(),
            solo_primer_caso=_bool(e("SOLO_PRIMER_CASO", ""), d.solo_primer_caso),
            reports_api_version=e("REPORTS_API_VERSION", d.reports_api_version).strip(),
            filtro_planes=e("FILTRO_PLANES", "").strip(),
            incluir_inactivos=_bool(e("INCLUIR_INACTIVOS", ""), d.incluir_inactivos),
            reports_output_file=e("REPORTS_OUTPUT_FILE", d.reports_output_file).strip(),
        )

    # Mapeo campo -> variable de .env (usado al guardar)
    ENV_KEYS = {
        "azdo_url": "AZDO_URL",
        "project": "PROJECT",
        "api_version": "API_VERSION",
        "use_system_certs": "USE_SYSTEM_CERTS",
        "verify_ssl": "VERIFY_SSL",
        "test_plan_name": "TEST_PLAN_NAME",
        "plan_id": "PLAN_ID",
        "suite_id": "SUITE_ID",
        "excel_file": "EXCEL_FILE",
        "excel_sheet_name": "EXCEL_SHEET_NAME",
        "solo_primer_caso": "SOLO_PRIMER_CASO",
        "reports_api_version": "REPORTS_API_VERSION",
        "filtro_planes": "FILTRO_PLANES",
        "incluir_inactivos": "INCLUIR_INACTIVOS",
        "reports_output_file": "REPORTS_OUTPUT_FILE",
    }

    def save_to_env(self, env_file: Path = ENV_FILE) -> None:
        """Actualiza (o crea) `.env` conservando comentarios y claves ajenas.
        Nunca escribe el PAT."""
        nuevos = {}
        for campo in fields(self):
            valor = asdict(self)[campo.name]
            if isinstance(valor, bool):
                valor = "true" if valor else "false"
            nuevos[self.ENV_KEYS[campo.name]] = str(valor)

        lineas = env_file.read_text(encoding="utf-8").splitlines() if env_file.exists() else []
        pendientes = dict(nuevos)
        salida = []
        for linea in lineas:
            clave = linea.split("=", 1)[0].strip()
            if "=" in linea and not linea.lstrip().startswith("#") and clave in pendientes:
                salida.append(f"{clave}={pendientes.pop(clave)}")
            else:
                salida.append(linea)
        salida.extend(f"{k}={v}" for k, v in pendientes.items())
        env_file.write_text("\n".join(salida) + "\n", encoding="utf-8")


def pat_desde_entorno() -> str:
    return os.environ.get("AZDO_PAT", "").strip()

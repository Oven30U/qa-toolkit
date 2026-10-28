"""Rutas del proyecto (independientes del directorio desde donde se ejecute)."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"
OUTPUT_DIR = PROJECT_ROOT / "output"
LOGS_DIR = PROJECT_ROOT / "logs"
ASSETS_DIR = PROJECT_ROOT / "assets"
POWERBI_DIR = ASSETS_DIR / "powerbi"


def asegurar_directorios():
    for carpeta in (OUTPUT_DIR, LOGS_DIR):
        carpeta.mkdir(parents=True, exist_ok=True)

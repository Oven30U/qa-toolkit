"""Logging: archivo rotativo + cola para el panel de la GUI."""

from __future__ import annotations

import logging
import logging.handlers
import queue
from logging.handlers import RotatingFileHandler

from qa_toolkit.core.paths import LOGS_DIR, asegurar_directorios

LOGGER_NAME = "qa_toolkit"
_FORMATO = "%(asctime)s | %(levelname)-7s | %(message)s"


def setup_logging(log_queue: "queue.Queue[logging.LogRecord] | None" = None) -> logging.Logger:
    asegurar_directorios()
    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    logger.propagate = False

    archivo = RotatingFileHandler(
        LOGS_DIR / "qa_toolkit.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    archivo.setFormatter(logging.Formatter(_FORMATO))
    logger.addHandler(archivo)

    if log_queue is not None:
        logger.addHandler(logging.handlers.QueueHandler(log_queue))
    return logger


def get_logger(nombre: str = "") -> logging.Logger:
    return logging.getLogger(f"{LOGGER_NAME}.{nombre}" if nombre else LOGGER_NAME)

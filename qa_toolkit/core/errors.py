"""Excepciones del dominio. Los servicios las lanzan; la UI las muestra."""


class QAToolkitError(Exception):
    """Base de todos los errores controlados de la aplicacion."""


class ConfigError(QAToolkitError):
    """Falta configuracion o es invalida."""


class ExcelError(QAToolkitError):
    """Problema leyendo o validando un Excel."""


class AzdoError(QAToolkitError):
    """Error devuelto por Azure DevOps o de comunicacion con el servidor."""

    def __init__(self, message, *, status=None, url=None, operation=None):
        super().__init__(message)
        self.status = status
        self.url = url
        self.operation = operation

    def detalle(self):
        partes = []
        if self.operation:
            partes.append(f"Operacion: {self.operation}")
        if self.status:
            partes.append(f"HTTP: {self.status}")
        if self.url:
            partes.append(f"URL: {self.url}")
        partes.append(f"Mensaje: {self}")
        return "\n".join(partes)


class CancelledError(QAToolkitError):
    """El usuario cancelo la tarea en curso."""

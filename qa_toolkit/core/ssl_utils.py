"""Certificados: usa el almacen del sistema (p. ej. CA interna corporativa en Windows)."""

from __future__ import annotations

_aplicado = False


def usar_certificados_del_sistema() -> bool:
    """Inyecta `truststore` una sola vez. Devuelve True si quedo activo.

    Debe llamarse ANTES de abrir la primera conexion HTTPS.
    """
    global _aplicado
    if _aplicado:
        return True
    try:
        import truststore
    except ImportError:
        return False
    truststore.inject_into_ssl()
    _aplicado = True
    return True


def silenciar_advertencias_ssl() -> None:
    import urllib3

    urllib3.disable_warnings()

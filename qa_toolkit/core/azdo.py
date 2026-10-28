"""
Cliente HTTP unico para Azure DevOps (Services y Server on-premise).

Lo comparten todos los modulos. No imprime ni corta el programa: lanza
`AzdoError` con el detalle y deja que la capa superior decida.
"""

from __future__ import annotations

from urllib.parse import quote

import requests
from requests.auth import HTTPBasicAuth

from qa_toolkit.core.errors import AzdoError
from qa_toolkit.core.ssl_utils import silenciar_advertencias_ssl


def _mensaje(response: requests.Response) -> str:
    try:
        contenido = response.json()
        if isinstance(contenido, dict):
            return str(contenido.get("message", contenido))
        return str(contenido)
    except ValueError:
        return response.text[:300]


class AzureDevOpsClient:
    def __init__(
        self,
        base_url: str,
        project: str,
        pat: str,
        api_version: str = "5.1",
        verify_ssl: bool = True,
        timeout: int = 60,
    ):
        if not base_url or not project:
            raise AzdoError("Falta la URL de Azure DevOps o el nombre del proyecto.")
        if not pat:
            raise AzdoError("Falta el Personal Access Token (PAT). Ingresalo en la pestaña Conexión.")
        self.base_url = base_url.rstrip("/")
        self.project = project
        self.project_encoded = quote(project, safe="")
        self.api_version = api_version
        self.timeout = timeout
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth("", pat)
        self.session.headers.update({"Accept": "application/json"})
        self.session.verify = verify_ssl
        if not verify_ssl:
            silenciar_advertencias_ssl()

    # ------------------------------------------------------------ helpers
    def url(self, path: str, *, with_project: bool = True) -> str:
        prefijo = f"{self.base_url}/{self.project_encoded}" if with_project else self.base_url
        return f"{prefijo}/{path.lstrip('/')}"

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json=None,
        headers: dict | None = None,
        operation: str = "",
        with_project: bool = True,
        ok: tuple = (200, 201),
    ) -> requests.Response:
        query = {"api-version": self.api_version}
        if params:
            query.update(params)
        try:
            r = self.session.request(
                method,
                self.url(path, with_project=with_project),
                params=query,
                json=json,
                headers=headers,
                timeout=self.timeout,
            )
        except requests.exceptions.SSLError as e:
            raise AzdoError(
                "Error de certificado SSL. Probá activar 'Usar certificados del sistema' "
                f"o desactivar 'Verificar SSL' en la pestaña Conexión.\n{e}",
                operation=operation,
            ) from e
        except requests.exceptions.RequestException as e:
            raise AzdoError(f"No se pudo conectar con el servidor: {e}", operation=operation) from e

        if "text/html" in r.headers.get("Content-Type", ""):
            raise AzdoError(
                "El servidor devolvió una página de login. Revisá el PAT y la URL.",
                status=r.status_code,
                url=r.url,
                operation=operation,
            )
        if r.status_code == 401:
            raise AzdoError(
                "El PAT es inválido, venció o no tiene los permisos necesarios.",
                status=401,
                url=r.url,
                operation=operation,
            )
        if r.status_code == 403:
            raise AzdoError(
                "Sin permisos para esta operación. Revisá los scopes del PAT.",
                status=403,
                url=r.url,
                operation=operation,
            )
        if r.status_code == 404:
            raise AzdoError(
                f"No encontrado (404). Revisá URL, proyecto, IDs o versión de API. {_mensaje(r)}",
                status=404,
                url=r.url,
                operation=operation,
            )
        if r.status_code not in ok:
            raise AzdoError(_mensaje(r), status=r.status_code, url=r.url, operation=operation)
        return r

    def get_json(self, path: str, **kw) -> dict:
        return self.request("GET", path, **kw).json()

    def get_paged(self, path: str, page_size: int = 200, **kw) -> list:
        """Recorre un endpoint paginado con $top/$skip."""
        items, skip = [], 0
        while True:
            params = {"$top": page_size, "$skip": skip}
            valores = self.get_json(path, params=params, **kw).get("value", [])
            items.extend(valores)
            if len(valores) < page_size:
                return items
            skip += page_size

    # ------------------------------------------------- operaciones comunes
    def validar_conexion(self) -> dict:
        """Valida PAT + proyecto. Devuelve el JSON del proyecto."""
        return self.get_json(
            f"/_apis/projects/{self.project_encoded}",
            operation="validar el PAT y el proyecto",
            with_project=False,
        )

    def obtener_work_item(self, work_item_id: int) -> dict:
        return self.get_json(
            f"/_apis/wit/workitems/{work_item_id}",
            operation=f"consultar Work Item {work_item_id}",
        )

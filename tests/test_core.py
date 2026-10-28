import pytest
import requests

from qa_toolkit.core.azdo import AzureDevOpsClient
from qa_toolkit.core.config import Settings
from qa_toolkit.core.errors import AzdoError


def test_cliente_exige_pat():
    with pytest.raises(AzdoError, match="PAT"):
        AzureDevOpsClient("https://x", "P", "")


def test_url_codifica_proyecto():
    c = AzureDevOpsClient("https://x/col/", "Mi Proyecto", "pat")
    assert c.url("/_apis/a") == "https://x/col/Mi%20Proyecto/_apis/a"


def _resp(status, ctype="application/json", body=b"{}"):
    r = requests.Response()
    r.status_code, r._content = status, body
    r.headers["Content-Type"] = ctype
    return r


@pytest.mark.parametrize("status,texto", [(401, "PAT"), (403, "permisos"), (404, "404")])
def test_errores_http(monkeypatch, status, texto):
    c = AzureDevOpsClient("https://x", "P", "pat")
    monkeypatch.setattr(c.session, "request", lambda *a, **k: _resp(status))
    with pytest.raises(AzdoError, match=texto):
        c.get_json("/_apis/a")


def test_pagina_html_es_login(monkeypatch):
    c = AzureDevOpsClient("https://x", "P", "pat")
    monkeypatch.setattr(c.session, "request", lambda *a, **k: _resp(200, "text/html"))
    with pytest.raises(AzdoError, match="login"):
        c.get_json("/_apis/a")


def test_paginado(monkeypatch):
    c = AzureDevOpsClient("https://x", "P", "pat")
    paginas = iter([{"value": list(range(200))}, {"value": [1, 2]}])
    import json

    monkeypatch.setattr(
        c.session, "request", lambda *a, **k: _resp(200, body=json.dumps(next(paginas)).encode())
    )
    assert len(c.get_paged("/_apis/a")) == 202


def test_save_to_env_conserva_y_no_guarda_pat(tmp_path):
    env = tmp_path / ".env"
    env.write_text("# comentario\nOTRA=1\nPROJECT=viejo\n", encoding="utf-8")
    Settings(azdo_url="https://u", project="nuevo", plan_id=5).save_to_env(env)
    txt = env.read_text(encoding="utf-8")
    assert "# comentario" in txt and "OTRA=1" in txt
    assert "PROJECT=nuevo" in txt and "PLAN_ID=5" in txt and "PAT" not in txt

import pytest
from fastapi.testclient import TestClient

from app.api.v1 import analyze as analyze_module
from app.main import app
from app.redirects import RedirectTrace

client = TestClient(app)


@pytest.fixture(autouse=True)
def sin_red(monkeypatch):
    """Los tests del endpoint no deben salir a internet: por defecto la
    trazabilidad se neutraliza y cada test que la necesite inyecta su traza."""
    monkeypatch.setattr(analyze_module, "resolve_chain", RedirectTrace.identity)


def _traza(chain, resolved=True, reason=""):
    return lambda url: RedirectTrace(tuple(chain), resolved, reason)


def test_analyze_returns_green_for_safe_short_url():
    response = client.post("/v1/analyze", json={"url": "https://example.com"})
    assert response.status_code == 200
    body = response.json()
    assert body["verdict"] == "green"
    assert body["score"] == 0
    assert body["reasons"] == []


def test_analyze_returns_yellow_for_long_url():
    long_url = "https://example.com/" + "x" * 200
    response = client.post("/v1/analyze", json={"url": long_url})
    assert response.status_code == 200
    body = response.json()
    assert body["verdict"] == "yellow"
    assert body["score"] > 0
    assert any("caracteres" in r for r in body["reasons"])


def test_analyze_returns_red_when_two_signals_add_up():
    # IP literal (40) + URL larga (30) = 70, por encima del umbral de rojo.
    url = "http://192.168.1.10/" + "x" * 120
    response = client.post("/v1/analyze", json={"url": url})
    assert response.status_code == 200
    body = response.json()
    assert body["verdict"] == "red"
    assert body["score"] == 70
    assert len(body["reasons"]) == 2


def test_analyze_rejects_invalid_url():
    response = client.post("/v1/analyze", json={"url": "no-es-una-url"})
    assert response.status_code == 422


def test_las_heuristicas_corren_sobre_la_url_terminal(monkeypatch):
    # El acortador es inocuo; el destino tiene IP literal (40) + URL larga (30).
    destino = "http://192.168.1.10/" + "x" * 120
    monkeypatch.setattr(
        analyze_module, "resolve_chain", _traza(["https://bit.ly/x8k2m", destino])
    )
    body = client.post("/v1/analyze", json={"url": "https://bit.ly/x8k2m"}).json()
    assert body["verdict"] == "red"
    assert body["final_url"] == destino
    assert body["redirects"]["hops"] == 1
    assert body["redirects"]["rewrote_url"] is True


def test_expone_la_cadena_completa_no_solo_el_destino(monkeypatch):
    cadena = ["https://a.example/", "https://b.example/", "https://c.example/"]
    monkeypatch.setattr(analyze_module, "resolve_chain", _traza(cadena))
    body = client.post("/v1/analyze", json={"url": cadena[0]}).json()
    assert body["redirects"]["chain"] == cadena
    assert body["redirects"]["resolved"] is True


def test_cadena_no_resuelta_se_reporta_en_las_razones(monkeypatch):
    monkeypatch.setattr(
        analyze_module,
        "resolve_chain",
        _traza(["https://a.example/"], resolved=False, reason="se supero el limite de 10 saltos"),
    )
    body = client.post("/v1/analyze", json={"url": "https://a.example/"}).json()
    assert body["redirects"]["resolved"] is False
    assert any("no resuelta" in r for r in body["reasons"])

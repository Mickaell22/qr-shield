import pytest
from fastapi.testclient import TestClient

from app import cache, urlhaus
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


def test_la_respuesta_trae_el_desglose_por_capa():
    body = client.post("/v1/analyze", json={"url": "https://example.com"}).json()
    metrics = body["metrics"]
    assert [c["layer"] for c in metrics["layers"]] == ["redirects", "L1"]
    assert metrics["total_ms"] >= 0
    # Nadie sumo puntos ni corto: el verde lo emite la cascada, no una capa.
    assert metrics["deciding_layer"] == "cascade"


def test_las_metricas_atribuyen_el_veredicto_a_la_capa_que_sumo():
    url = "http://192.168.1.10/" + "x" * 120
    body = client.post("/v1/analyze", json={"url": url}).json()
    metrics = body["metrics"]
    l1 = next(c for c in metrics["layers"] if c["layer"] == "L1")
    assert metrics["deciding_layer"] == "L1"
    assert l1["score"] == 70
    assert l1["hits"] == 2


def test_las_metricas_registran_los_saltos_de_la_trazabilidad(monkeypatch):
    cadena = ["https://a.example/", "https://b.example/", "https://c.example/"]
    monkeypatch.setattr(analyze_module, "resolve_chain", _traza(cadena))
    body = client.post("/v1/analyze", json={"url": cadena[0]}).json()
    redirects = next(c for c in body["metrics"]["layers"] if c["layer"] == "redirects")
    assert redirects["hits"] == 2


@pytest.fixture
def cache_activa(monkeypatch):
    """Cache L2 encendida con un doble en memoria: devuelve lo que se le ponga
    en `guardado` y anota lo que el motor intenta escribir en `escrito`."""
    estado = {"guardado": None, "escrito": []}
    monkeypatch.setattr(cache, "enabled", lambda: True)
    monkeypatch.setattr(cache, "lookup", lambda url: estado["guardado"])
    monkeypatch.setattr(
        cache, "store", lambda url, **kwargs: estado["escrito"].append((url, kwargs)) or True
    )
    return estado


def test_un_hit_de_cache_corta_la_cascada(cache_activa):
    cache_activa["guardado"] = cache.CachedVerdict(
        verdict="red", score=85, reasons=["senal previa"], source_layer="L1"
    )
    body = client.post("/v1/analyze", json={"url": "https://example.com"}).json()

    # La URL es inocua para L1: el rojo solo puede venir de la cache.
    assert body["verdict"] == "red"
    assert body["score"] == 85
    assert body["metrics"]["deciding_layer"] == "L2"
    l2 = next(c for c in body["metrics"]["layers"] if c["layer"] == "L2")
    assert l2["short_circuited"] is True
    assert any("desde la cache" in r for r in body["reasons"])


def test_un_miss_guarda_el_veredicto_con_la_capa_que_lo_emitio(cache_activa):
    url = "http://192.168.1.10/" + "x" * 120
    body = client.post("/v1/analyze", json={"url": url}).json()

    assert body["metrics"]["deciding_layer"] == "L1"
    (guardada, datos), = cache_activa["escrito"]
    assert guardada == body["final_url"]
    assert datos["verdict"] == "red"
    assert datos["score"] == 70
    # La cache no puede figurar como origen del veredicto que ella misma guarda.
    assert datos["source_layer"] == "L1"


def test_no_se_cachea_un_veredicto_de_cadena_sin_resolver(cache_activa, monkeypatch):
    monkeypatch.setattr(
        analyze_module,
        "resolve_chain",
        _traza(["https://a.example/"], resolved=False, reason="bucle de redirecciones"),
    )
    client.post("/v1/analyze", json={"url": "https://a.example/"})
    # El analisis corrio sobre una URL intermedia: guardarlo serviria un
    # veredicto parcial como definitivo.
    assert cache_activa["escrito"] == []


def test_con_la_cache_apagada_no_aparece_la_capa_l2(monkeypatch):
    monkeypatch.setattr(cache, "enabled", lambda: False)
    body = client.post("/v1/analyze", json={"url": "https://example.com"}).json()
    assert [c["layer"] for c in body["metrics"]["layers"]] == ["redirects", "L1"]
    assert body["metrics"]["deciding_layer"] == "cascade"


def test_una_url_listada_en_urlhaus_es_roja_y_la_decide_l3(monkeypatch):
    monkeypatch.setattr(cache, "DATABASE_URL", "")
    monkeypatch.setattr(urlhaus, "_urls", frozenset({"https://example.com/descarga"}))
    response = client.post("/v1/analyze", json={"url": "https://example.com/descarga"})
    body = response.json()
    assert body["verdict"] == "red"
    assert body["score"] == 100
    assert body["metrics"]["deciding_layer"] == "L3"
    l3 = next(c for c in body["metrics"]["layers"] if c["layer"] == "L3")
    assert l3["short_circuited"]


def test_sin_feed_cargado_l3_no_figura_en_las_metricas(monkeypatch):
    monkeypatch.setattr(cache, "DATABASE_URL", "")
    monkeypatch.setattr(urlhaus, "_urls", None)
    body = client.post("/v1/analyze", json={"url": "https://example.com"}).json()
    assert "L3" not in [c["layer"] for c in body["metrics"]["layers"]]

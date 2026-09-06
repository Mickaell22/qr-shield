import json
import logging

import pytest

from app import telemetry
from app.telemetry import AnalysisMetrics


def _metricas(*capas):
    """Arma un recolector con capas ya medidas: (nombre, score, service)."""
    metrics = AnalysisMetrics()
    for layer, score, service in capas:
        with metrics.measure(layer, service=service) as medicion:
            medicion.score = score
    return metrics


def _registro(metrics, **overrides):
    datos = {
        "url": "https://example.com/",
        "verdict": "green",
        "score": 0,
        "redirect_hops": 0,
        "redirect_rewrote_url": False,
        "redirect_resolved": True,
    }
    return metrics.record(**{**datos, **overrides})


def test_measure_registra_las_capas_en_orden_con_su_duracion():
    metrics = _metricas(("redirects", 0, None), ("L1", 30, None))
    assert [m.layer for m in metrics.layers] == ["redirects", "L1"]
    assert all(m.duration_ms >= 0 for m in metrics.layers)


def test_measure_mide_la_capa_aunque_el_bloque_falle():
    metrics = AnalysisMetrics()
    with pytest.raises(ValueError):
        with metrics.measure("L4"):
            raise ValueError("la capa externa se cayo")
    # Sin esto una capa que revienta desaparece del registro y el tiempo que
    # consumio antes de fallar no se puede atribuir a nadie.
    assert [m.layer for m in metrics.layers] == ["L4"]


def test_la_capa_responsable_es_la_ultima_que_aporto_puntos():
    metrics = _metricas(("redirects", 0, None), ("L1", 30, None), ("L2", 0, None))
    assert metrics.deciding_layer == "L1"


def test_sin_puntos_el_veredicto_es_de_la_cascada_no_de_una_capa():
    # Verde: la cascada se agoto sin que nadie sumara ni cortara. Atribuirlo a
    # la ultima capa contaria como resuelta ahi una consulta que no resolvio.
    metrics = _metricas(("redirects", 0, None), ("L1", 0, None), ("L2", 0, None))
    assert metrics.deciding_layer == "cascade"


def test_la_capa_que_corta_la_cascada_manda_sobre_las_que_sumaron():
    metrics = AnalysisMetrics()
    with metrics.measure("L1") as medicion:
        medicion.score = 30
    with metrics.measure("L2") as medicion:
        medicion.short_circuited = True
    # Un hit de cache resuelve el analisis aunque no sume puntos propios.
    assert metrics.deciding_layer == "L2"


def test_sin_capas_no_hay_responsable():
    assert AnalysisMetrics().deciding_layer == "none"


def test_solo_se_listan_los_servicios_externos_consultados():
    metrics = _metricas(("L1", 0, None), ("L4", 0, "google_safe_browsing"))
    assert metrics.services == ["google_safe_browsing"]


def test_el_registro_anonimiza_la_url_por_defecto(monkeypatch):
    monkeypatch.setattr(telemetry, "METRICS_LOG_URLS", False)
    registro = _registro(_metricas(("L1", 0, None)), url="https://pagos-banc0.xyz/login")
    assert registro["url"].startswith("sha256:")
    assert "pagos-banc0" not in registro["url"]


def test_la_url_completa_solo_se_registra_si_se_pide(monkeypatch):
    monkeypatch.setattr(telemetry, "METRICS_LOG_URLS", True)
    registro = _registro(_metricas(("L1", 0, None)), url="https://pagos-banc0.xyz/login")
    assert registro["url"] == "https://pagos-banc0.xyz/login"


def test_el_registro_trae_lo_que_exige_el_requisito():
    metrics = _metricas(("redirects", 0, None), ("L1", 70, None))
    registro = _registro(
        metrics, verdict="red", score=70, redirect_hops=2, redirect_rewrote_url=True
    )

    assert registro["verdict"] == "red"
    assert registro["score"] == 70
    assert registro["deciding_layer"] == "L1"
    assert registro["total_ms"] >= sum(c["duration_ms"] for c in registro["layers"])
    assert registro["redirects"] == {"hops": 2, "rewrote_url": True, "resolved": True}
    assert registro["timestamp"].endswith("+00:00")
    assert isinstance(registro["tracing_enabled"], bool)


def test_emit_escribe_una_linea_json_parseable(caplog):
    with caplog.at_level(logging.INFO, logger="motor.metrics"):
        registro = _metricas(("L1", 0, None)).emit(
            url="https://example.com/",
            verdict="green",
            score=0,
            redirect_hops=0,
            redirect_rewrote_url=False,
            redirect_resolved=True,
        )
    # El log es la fuente del reporte de validacion: si no parsea, no hay metricas.
    assert json.loads(caplog.records[0].message) == registro

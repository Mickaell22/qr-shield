"""Tests de las metricas del benchmark: si el calculo esta mal, el reporte que
va a la tesis esta mal aunque el motor funcione."""

import csv

import pytest

import benchmark as bm


def _fila(label, verdict, url=None, rewrote=False):
    return {
        "url": url or f"https://{label}-{verdict}.example/",
        "label": label,
        "verdict": verdict,
        "deciding_layer": "L1",
        "total_ms": 10.0,
        "resolved": True,
        "rewrote_url": rewrote,
        "layers": [{"layer": "L1", "duration_ms": 1.0}],
    }


def test_matriz_de_confusion_y_metricas_por_criterio():
    filas = [
        _fila("malicious", "red", "https://a/"),
        _fila("malicious", "yellow", "https://b/"),
        _fila("malicious", "green", "https://c/"),
        _fila("legit", "yellow", "https://d/"),
        _fila("legit", "green", "https://e/"),
    ]
    estricto = bm.confusion(filas, bm.CRITERIA["estricto"])
    assert (estricto["tp"], estricto["fn"], estricto["fp"], estricto["tn"]) == (1, 2, 0, 2)
    assert estricto["precision"] == 1.0
    assert estricto["recall"] == pytest.approx(1 / 3, abs=1e-4)

    amplio = bm.confusion(filas, bm.CRITERIA["amplio"])
    assert (amplio["tp"], amplio["fn"], amplio["fp"], amplio["tn"]) == (2, 1, 1, 1)
    assert amplio["fpr"] == 0.5


def test_sin_positivos_la_precision_queda_indefinida_y_no_divide_por_cero():
    c = bm.confusion([_fila("legit", "green")], bm.CRITERIA["estricto"])
    assert c["precision"] is None
    assert c["f1"] is None


def test_los_errores_no_cuentan_como_verdes():
    filas = [_fila("malicious", "red"), {**_fila("malicious", "error"), "layers": []}]
    resumen = bm.summarize_mode(filas)
    assert resumen["errores"] == 1
    assert resumen["criterios"]["estricto"]["recall"] == 1.0


def test_percentil_por_rango_mas_cercano():
    valores = list(range(1, 101))
    assert bm.percentile(valores, 50) == 50
    assert bm.percentile(valores, 95) == 95
    assert bm.percentile([7], 95) == 7
    assert bm.percentile([], 95) is None


def test_mcnemar_exacto():
    # Valor de referencia: binomial(n=10, p=0.5), P(X<=1) * 2 = 22/1024.
    assert bm.mcnemar_p(9, 1) == pytest.approx(22 / 1024)
    assert bm.mcnemar_p(0, 0) == 1.0
    assert bm.mcnemar_p(5, 5) == 1.0


def test_la_comparacion_es_pareada_por_url():
    con = [
        _fila("malicious", "red", "https://qr/1", rewrote=True),
        _fila("malicious", "green", "https://qr/2"),
        _fila("malicious", "red", "https://qr/3"),
    ]
    sin = [
        _fila("malicious", "green", "https://qr/1"),
        _fila("malicious", "green", "https://qr/2"),
        {**_fila("malicious", "error", "https://qr/3"), "layers": []},
    ]
    comp = bm.compare(con, sin)
    # La URL que fallo en una corrida sale de la comparacion.
    assert comp["pares"] == 2
    mal = comp["estricto"]["malicious"]
    assert mal["marcadas_solo_con_trazabilidad"] == 1
    assert mal["marcadas_solo_sin_trazabilidad"] == 0
    red = comp["estricto"]["maliciosas_redirigidas"]
    assert (red["n"], red["recall_con"], red["recall_sin"]) == (1, 1.0, 0.0)


def test_el_dataset_es_reproducible_y_descarta_urls_invalidas(tmp_path):
    phishing = tmp_path / "phishtank.csv"
    with phishing.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["phish_id", "url", "verified"])
        for i in range(20):
            w.writerow([i, f"http://phish{i}.example/login", "yes"])
        w.writerow([99, "no-es-una-url", "yes"])
        w.writerow([98, "http://no-verificada.example/", "no"])
    legit = tmp_path / "tranco.csv"
    legit.write_text("".join(f"{i},sitio{i}.example\n" for i in range(20)))

    a = bm.build_dataset(phishing, legit, n=10, seed=7)
    assert a == bm.build_dataset(phishing, legit, n=10, seed=7)
    assert len(a) == 20
    urls = {f["url"] for f in a}
    assert "no-es-una-url" not in urls
    assert "http://no-verificada.example/" not in urls

    with pytest.raises(SystemExit):
        bm.build_dataset(phishing, legit, n=50, seed=7)


def test_el_reporte_markdown_se_renderiza():
    filas = [_fila("malicious", "red"), _fila("legit", "green")]
    rep = {
        "motor_version": "0.0.0",
        "fecha": "2026-01-01T00:00:00+00:00",
        "dataset": {"archivo": "d.csv", "sha256": "0" * 64, "por_clase": {"malicious": 1}},
        "configuracion": {"workers": 1, "capas": ["L1"]},
        "duracion_s": 1.0,
        "con_trazabilidad": bm.summarize_mode(filas),
        "sin_trazabilidad": bm.summarize_mode(filas),
        "comparacion": bm.compare(filas, filas),
    }
    md = bm.render_markdown(rep)
    assert "| Con trazabilidad |" in md
    assert "McNemar" in md

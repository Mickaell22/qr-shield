from app.detectors.l1_heuristics import HeuristicResult, run_l1
from app.scoring import RED_THRESHOLD, SCORE_MAX, evaluate


def hit(score: int) -> HeuristicResult:
    return HeuristicResult(triggered=True, score=score, reason="test")


def test_sin_hits_es_verde():
    assert evaluate([]) == (0, "green")


def test_un_hit_debil_es_amarillo():
    assert evaluate([hit(25)]) == (25, "yellow")


def test_la_heuristica_mas_fuerte_sola_no_llega_a_rojo():
    # punycode vale 50: por si sola no debe marcar rojo (dominios IDN legitimos).
    assert evaluate([hit(50)]) == (50, "yellow")


def test_justo_debajo_del_umbral_es_amarillo():
    assert evaluate([hit(RED_THRESHOLD - 1)])[1] == "yellow"


def test_en_el_umbral_es_rojo():
    assert evaluate([hit(RED_THRESHOLD)])[1] == "red"


def test_dos_senales_acumulan_a_rojo():
    # IP literal (40) + URL larga (30) = 70
    assert evaluate([hit(40), hit(30)]) == (70, "red")


def test_el_score_se_topa_en_el_maximo():
    score, verdict = evaluate([hit(50)] * 5)
    assert score == SCORE_MAX
    assert verdict == "red"


def test_url_maliciosa_real_suma_a_rojo():
    score, verdict = evaluate(run_l1("https://xn--80ak6aa92e.tk/login"))
    assert score == 85  # punycode (50) + TLD sospechoso (35)
    assert verdict == "red"

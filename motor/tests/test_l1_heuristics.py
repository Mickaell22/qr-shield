from app.detectors.l1_heuristics import (
    IP_LITERAL_SCORE,
    PUNYCODE_SCORE,
    SHORTENER_SCORE,
    SUSPICIOUS_TLD_SCORE,
    URL_LENGTH_SCORE,
    URL_LENGTH_THRESHOLD,
    check_ip_literal,
    check_punycode,
    check_shortener,
    check_suspicious_tld,
    check_url_length,
    run_l1,
)


def test_url_length_short_url_does_not_trigger():
    result = check_url_length("https://ejemplo.com")
    assert result.triggered is False
    assert result.score == 0
    assert result.reason == ""


def test_url_length_at_threshold_does_not_trigger():
    padding = "a" * (URL_LENGTH_THRESHOLD - len("https://"))
    url = "https://" + padding
    assert len(url) == URL_LENGTH_THRESHOLD
    assert check_url_length(url).triggered is False


def test_url_length_just_above_threshold_triggers():
    padding = "a" * (URL_LENGTH_THRESHOLD + 1 - len("https://"))
    url = "https://" + padding
    assert len(url) == URL_LENGTH_THRESHOLD + 1
    result = check_url_length(url)
    assert result.triggered is True
    assert result.score == URL_LENGTH_SCORE
    assert str(URL_LENGTH_THRESHOLD) in result.reason


def test_ip_literal_ipv4_host_triggers():
    result = check_ip_literal("http://192.168.1.1/login")
    assert result.triggered is True
    assert result.score == IP_LITERAL_SCORE
    assert "192.168.1.1" in result.reason


def test_ip_literal_ipv6_host_triggers():
    result = check_ip_literal("http://[2001:db8::1]/login")
    assert result.triggered is True
    assert result.score == IP_LITERAL_SCORE


def test_ip_literal_domain_host_does_not_trigger():
    result = check_ip_literal("https://ejemplo.com/login")
    assert result.triggered is False
    assert result.score == 0
    assert result.reason == ""


def test_shortener_known_host_triggers():
    result = check_shortener("https://bit.ly/abc123")
    assert result.triggered is True
    assert result.score == SHORTENER_SCORE
    assert "bit.ly" in result.reason


def test_shortener_ignores_www_and_case():
    result = check_shortener("https://WWW.TinyURL.com/xyz")
    assert result.triggered is True
    assert result.score == SHORTENER_SCORE


def test_shortener_normal_domain_does_not_trigger():
    result = check_shortener("https://ejemplo.com/abc")
    assert result.triggered is False
    assert result.score == 0
    assert result.reason == ""


def test_suspicious_tld_freenom_host_triggers():
    result = check_suspicious_tld("http://banco-seguro.tk/login")
    assert result.triggered is True
    assert result.score == SUSPICIOUS_TLD_SCORE
    assert ".tk" in result.reason


def test_suspicious_tld_ignores_case():
    assert check_suspicious_tld("http://EJEMPLO.XYZ/x").triggered is True


def test_suspicious_tld_common_tld_does_not_trigger():
    result = check_suspicious_tld("https://ejemplo.com/login")
    assert result.triggered is False
    assert result.score == 0
    assert result.reason == ""


def test_suspicious_tld_ip_literal_does_not_trigger():
    assert check_suspicious_tld("http://192.168.1.1/login").triggered is False


def test_punycode_encoded_host_triggers():
    result = check_punycode("https://xn--80ak6aa92e.com/login")
    assert result.triggered is True
    assert result.score == PUNYCODE_SCORE
    assert "xn--" in result.reason


def test_punycode_unicode_host_triggers():
    # urlparse deja el host IDN sin convertir; la heuristica lo detecta igual.
    result = check_punycode("https://аpple.com/login")
    assert result.triggered is True
    assert result.score == PUNYCODE_SCORE


def test_punycode_ascii_host_does_not_trigger():
    result = check_punycode("https://apple.com/login")
    assert result.triggered is False
    assert result.score == 0
    assert result.reason == ""


def test_punycode_does_not_confuse_xn_inside_label():
    assert check_punycode("https://proxn--dat.com/x").triggered is False


def test_run_l1_returns_empty_for_safe_url():
    assert run_l1("https://ejemplo.com") == []


def test_run_l1_returns_hit_for_shortener():
    hits = run_l1("https://t.co/x")
    assert len(hits) == 1
    assert hits[0].score == SHORTENER_SCORE


def test_run_l1_returns_hit_for_ip_literal():
    hits = run_l1("http://10.0.0.5/pay")
    assert len(hits) == 1
    assert hits[0].score == IP_LITERAL_SCORE


def test_run_l1_returns_hit_for_long_url():
    long_url = "https://ejemplo.com/" + "x" * 200
    hits = run_l1(long_url)
    assert len(hits) == 1
    assert hits[0].triggered is True
    assert hits[0].score == URL_LENGTH_SCORE


def test_run_l1_returns_hit_for_suspicious_tld():
    hits = run_l1("http://pagos-uni.tk/login")
    assert len(hits) == 1
    assert hits[0].score == SUSPICIOUS_TLD_SCORE


def test_run_l1_acumula_varias_senales():
    hits = run_l1("http://xn--80ak6aa92e.tk/login")
    assert {h.score for h in hits} == {SUSPICIOUS_TLD_SCORE, PUNYCODE_SCORE}

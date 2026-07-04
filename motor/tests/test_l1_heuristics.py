from app.detectors.l1_heuristics import (
    IP_LITERAL_SCORE,
    SHORTENER_SCORE,
    URL_LENGTH_SCORE,
    URL_LENGTH_THRESHOLD,
    check_ip_literal,
    check_shortener,
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

from app.detectors.l1_heuristics import (
    URL_LENGTH_SCORE,
    URL_LENGTH_THRESHOLD,
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


def test_run_l1_returns_empty_for_safe_url():
    assert run_l1("https://ejemplo.com") == []


def test_run_l1_returns_hit_for_long_url():
    long_url = "https://ejemplo.com/" + "x" * 200
    hits = run_l1(long_url)
    assert len(hits) == 1
    assert hits[0].triggered is True
    assert hits[0].score == URL_LENGTH_SCORE

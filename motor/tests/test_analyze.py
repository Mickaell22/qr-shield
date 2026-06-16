from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


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


def test_analyze_rejects_invalid_url():
    response = client.post("/v1/analyze", json={"url": "no-es-una-url"})
    assert response.status_code == 422

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_stub_returns_green():
    response = client.post("/v1/analyze", json={"url": "https://example.com"})
    assert response.status_code == 200
    body = response.json()
    assert body["verdict"] == "green"
    assert body["score"] == 0
    assert body["reasons"] == []

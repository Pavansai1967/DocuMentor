from fastapi.testclient import TestClient

from app.main import create_app


def test_health():
    res = TestClient(create_app()).get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_routes_mounted():
    app = create_app()
    paths = set(app.openapi()["paths"])
    assert "/upload" in paths
    assert "/documents" in paths
    assert "/chat" in paths

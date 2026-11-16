"""CORS: the dashboard calls the API from the browser, so allowed origins
are configured, not hardcoded. Default is local development only."""
from fastapi.testclient import TestClient

from main import app


def test_allowed_origin_gets_cors_headers():
    client = TestClient(app)
    res = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert res.status_code == 200
    assert res.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_disallowed_origin_gets_no_cors_headers():
    client = TestClient(app)
    res = client.get("/health", headers={"Origin": "https://not-allowed.example"})
    assert res.status_code == 200
    assert "access-control-allow-origin" not in res.headers


def test_preflight_allows_claimkit_role_header():
    client = TestClient(app)
    res = client.options(
        "/documents/upload",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "X-ClaimKit-Role",
        },
    )
    assert res.status_code == 200
    assert res.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_cors_origins_come_from_env(monkeypatch):
    import importlib

    import main as main_module

    monkeypatch.setenv(
        "CORS_ORIGINS", "https://claimkit.vercel.app, http://localhost:3000"
    )
    try:
        importlib.reload(main_module)
        client = TestClient(main_module.app)
        res = client.get(
            "/health", headers={"Origin": "https://claimkit.vercel.app"}
        )
        assert res.status_code == 200
        assert (
            res.headers["access-control-allow-origin"]
            == "https://claimkit.vercel.app"
        )
    finally:
        monkeypatch.delenv("CORS_ORIGINS", raising=False)
        importlib.reload(main_module)

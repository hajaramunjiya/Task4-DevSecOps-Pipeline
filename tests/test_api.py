"""Integration tests for the HTTP API, using Flask's test client (no
real network socket needed - fast enough to run on every commit)."""
import pytest

from api.server import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_health_returns_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_security_headers_present_on_every_response(client):
    resp = client.get("/health")
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert "Content-Security-Policy" in resp.headers


def test_run_rejects_path_traversal_attempt(client):
    resp = client.post("/run", json={"input_path": "../../../../etc/passwd"})
    assert resp.status_code == 400


def test_run_rejects_missing_input_path(client):
    resp = client.post("/run", json={})
    assert resp.status_code == 400


def test_zone_rejects_non_numeric_id(client):
    resp = client.get("/zone/__import__('os')")
    assert resp.status_code == 400


def test_summary_returns_404_before_any_run(client):
    resp = client.get("/summary")
    assert resp.status_code == 404

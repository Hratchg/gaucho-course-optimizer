"""Regression tests for BUG-6 — 500 responses must carry CORS headers.

Starlette's ServerErrorMiddleware sits outside user middleware, so an
unhandled exception used to produce a bare text/plain 500 with no
Access-Control-Allow-Origin. The browser reported an opaque "Failed to fetch"
and the SPA could not distinguish a server fault from an offline client.
"""
from fastapi.testclient import TestClient

from api.dependencies import get_db
from api.main import app

ORIGIN = "https://www.coursepick.app"


def _client_with_broken_db() -> TestClient:
    """A client whose DB dependency raises, simulating a database outage."""

    def override_get_db():
        raise RuntimeError("connection to server failed: quota exceeded")

    app.dependency_overrides[get_db] = override_get_db
    # raise_server_exceptions=False makes TestClient return the 500 the browser
    # would see instead of re-raising the exception into the test.
    return TestClient(app, raise_server_exceptions=False)


def test_500_includes_cors_headers():
    """A failing endpoint still returns Access-Control-Allow-Origin."""
    client = _client_with_broken_db()
    try:
        response = client.get("/courses/search?q=MATH4A", headers={"Origin": ORIGIN})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    assert response.headers.get("access-control-allow-origin") == ORIGIN


def test_500_returns_json_with_error_id():
    """The error body is JSON and carries a correlation id for log lookup."""
    client = _client_with_broken_db()
    try:
        response = client.get("/courses/search?q=MATH4A", headers={"Origin": ORIGIN})
    finally:
        app.dependency_overrides.clear()

    assert response.headers["content-type"].startswith("application/json")
    body = response.json()
    assert body["detail"] == "Internal server error"
    assert len(body["error_id"]) == 12


def test_successful_response_still_has_cors(client):
    """The added middleware does not disturb the normal CORS path."""
    response = client.get("/health", headers={"Origin": ORIGIN})

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == ORIGIN

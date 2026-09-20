from fastapi.testclient import TestClient

from api.dependencies import get_db
from api.main import app


def test_ready_ok(client):
    """When the database responds to SELECT 1, /ready returns 200 ok."""
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_db_down():
    """When the database is unreachable, /ready returns 503 unavailable.

    Simulates DB downtime (e.g. Neon quota exceeded) with a session whose
    execute() raises — exactly what SQLAlchemy does when the server
    rejects connections.
    """

    class BrokenSession:
        def execute(self, *args, **kwargs):
            raise RuntimeError("connection to server failed: quota exceeded")

        def close(self):
            pass

    def override_get_db():
        yield BrokenSession()

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = TestClient(app).get("/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}

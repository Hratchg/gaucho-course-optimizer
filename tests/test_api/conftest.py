import pytest
from fastapi.testclient import TestClient

from api.dependencies import get_db
from api.main import app


@pytest.fixture
def client(db_session):
    """TestClient that injects the SAVEPOINT db_session into the FastAPI app.

    Uses app.dependency_overrides to replace get_db() with the existing
    SAVEPOINT session from conftest.py. This guarantees:
    - Tests use a real PostgreSQL session (catches dialect-specific bugs)
    - All DB changes roll back after each test (SAVEPOINT pattern)
    - No pollution between tests (override is cleared in teardown)
    """
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

"""Tests for GET /courses/search and GET /courses/{course_id}/professors.

All 8 behaviours from Plan 02-03, Task 1.
Uses FastAPI TestClient with dependency_overrides to mock the DB session.
"""
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.dependencies import get_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_prof(
    *,
    id: int = 1,
    name: str = "Test Prof",
    department: str = "CS",
    mean_gpa: float | None = 3.5,
    rmp_quality: float | None = 4.0,
    rmp_difficulty: float | None = 2.0,
    rmp_would_take_again: float | None = 80.0,
    rmp_num_ratings: int | None = 50,
    avg_sentiment: float | None = 0.3,
    quarters_taught: int = 4,
    keywords: list[str] | None = None,
    match_confidence: float | None = None,
    std_gpa: float | None = None,
    is_active_teacher: bool = False,
    recent_quarters: list[str] | None = None,
) -> dict:
    return {
        "id": id,
        "name": name,
        "department": department,
        "mean_gpa": mean_gpa,
        "std_gpa": std_gpa,
        "rmp_quality": rmp_quality,
        "rmp_difficulty": rmp_difficulty,
        "rmp_would_take_again": rmp_would_take_again,
        "rmp_num_ratings": rmp_num_ratings,
        "avg_sentiment": avg_sentiment,
        "quarters_taught": quarters_taught,
        "keywords": keywords or [],
        "match_confidence": match_confidence,
        "is_active_teacher": is_active_teacher,
        "recent_quarters": recent_quarters or [],
    }


def _make_course(*, id: int = 1, code: str = "CS 130A", title: str = "Data Structures", department: str = "CS") -> dict:
    return {"id": id, "code": code, "title": title, "department": department}



# ---------------------------------------------------------------------------
# Test 1: GET /courses/search?q=CS → 200 with correct keys
# ---------------------------------------------------------------------------

def test_search_returns_200_with_correct_keys(monkeypatch):
    courses = [_make_course(code="CS 130A"), _make_course(id=2, code="CS 130B", title="Algorithms")]
    monkeypatch.setattr("api.routers.courses.search_courses", lambda db, q: courses)

    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)
    resp = client.get("/courses/search?q=CS")

    try:
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2
        for item in data:
            assert "id" in item
            assert "code" in item
            assert "title" in item
            assert "department" in item
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Test 2: GET /courses/search?q=A$B → 422 (pattern violation)
# ---------------------------------------------------------------------------

def test_search_pattern_violation_returns_422():
    client = TestClient(app)
    resp = client.get("/courses/search?q=A$B")
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Test 3: GET /courses/search?q={101 chars} → 422 (max_length violation)
# ---------------------------------------------------------------------------

def test_search_max_length_violation_returns_422():
    long_q = "a" * 101
    client = TestClient(app)
    resp = client.get(f"/courses/search?q={long_q}")
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Test 4: GET /courses/{valid_id}/professors → 200, sorted descending by gaucho_score
# ---------------------------------------------------------------------------

def test_get_professors_sorted_by_gaucho_score(monkeypatch):
    profs = [
        _make_prof(id=1, name="Prof A", rmp_quality=3.0, mean_gpa=3.0),
        _make_prof(id=2, name="Prof B", rmp_quality=5.0, mean_gpa=4.0),
        _make_prof(id=3, name="Prof C", rmp_quality=1.0, mean_gpa=2.0),
    ]
    monkeypatch.setattr("api.routers.courses.get_professors_for_course", lambda db, course_id: profs)

    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)
    resp = client.get("/courses/1/professors")

    try:
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        scores = [item["gaucho_score"] for item in data]
        assert scores == sorted(scores, reverse=True), f"Not sorted descending: {scores}"
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Test 5: GET /courses/999999/professors → 404 when no professors exist
# ---------------------------------------------------------------------------

def test_get_professors_404_when_empty(monkeypatch):
    monkeypatch.setattr("api.routers.courses.get_professors_for_course", lambda db, course_id: [])

    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)
    resp = client.get("/courses/999999/professors")

    try:
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Test 6: avg_sentiment=0.0 → sentiment_factor=0.5 (VADER normalization)
# ---------------------------------------------------------------------------

def test_sentiment_factor_vader_normalization(monkeypatch):
    profs = [_make_prof(avg_sentiment=0.0)]
    monkeypatch.setattr("api.routers.courses.get_professors_for_course", lambda db, course_id: profs)

    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)
    resp = client.get("/courses/1/professors")

    try:
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["sentiment_factor"] == pytest.approx(0.5), (
            f"Expected sentiment_factor=0.5 for avg_sentiment=0.0, got {data[0]['sentiment_factor']}"
        )
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Test 7: rmp_quality=None → quality_factor is omitted, not scored as 0.5
# ---------------------------------------------------------------------------

def test_quality_factor_none_is_not_neutral(monkeypatch):
    profs = [_make_prof(rmp_quality=None, rmp_difficulty=None, avg_sentiment=None)]
    monkeypatch.setattr("api.routers.courses.get_professors_for_course", lambda db, course_id: profs)

    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)
    resp = client.get("/courses/1/professors")

    try:
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["quality_factor"] is None
        assert data[0]["has_rmp"] is False
        # GPA 3.5 / 4.0 = 0.875 → 87.5 when RMP factors are omitted
        assert data[0]["gaucho_score"] == pytest.approx(87.5)
    finally:
        app.dependency_overrides.clear()


def test_professors_are_paginated(monkeypatch):
    profs = [
        _make_prof(id=1, name="A", mean_gpa=4.0),
        _make_prof(id=2, name="B", mean_gpa=3.0),
        _make_prof(id=3, name="C", mean_gpa=2.0),
    ]
    monkeypatch.setattr("api.routers.courses.get_professors_for_course", lambda db, course_id: profs)
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)
    try:
        resp = client.get("/courses/1/professors?limit=2&offset=0")
        assert resp.status_code == 200
        assert resp.headers["X-Total-Count"] == "3"
        assert len(resp.json()) == 2
        page_two = client.get("/courses/1/professors?limit=2&offset=2")
        assert len(page_two.json()) == 1
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Test 8: GET /courses/search?q=physics is NOT matched by /{course_id}/professors
# (route order: /search must come before /{course_id}/professors)
# ---------------------------------------------------------------------------

def test_search_route_not_shadowed_by_course_id_route(monkeypatch):
    """Verifies /search is declared before /{course_id}/professors.

    If /{course_id}/professors came first, the router would try to parse
    "search" as an integer course_id and return 422 (int parse error).
    We expect either 200 or a query-string validation error (missing q param),
    NOT a 422 from int parsing of the literal string "search".
    """
    monkeypatch.setattr("api.routers.courses.search_courses", lambda db, q: [])

    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)
    # Hit /courses/search with q=physics — should reach the /search handler,
    # not try to parse "search" as a course_id integer.
    resp = client.get("/courses/search?q=physics")

    try:
        # The /search handler accepts q=physics (valid pattern), returns 200
        assert resp.status_code == 200, (
            f"Expected 200 (search route matched), got {resp.status_code}. "
            "This indicates /{course_id}/professors shadowed /search."
        )
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Test 9: avg_sentiment, std_gpa, match_confidence are passed through to response
# ---------------------------------------------------------------------------

def test_professor_response_includes_passthrough_fields(monkeypatch):
    """avg_sentiment, std_gpa, match_confidence from query are present in response."""
    prof = _make_prof(avg_sentiment=0.6, std_gpa=0.3, match_confidence=95)
    monkeypatch.setattr("api.routers.courses.get_professors_for_course", lambda db, cid: [prof])
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)
    try:
        resp = client.get("/courses/1/professors")
        assert resp.status_code == 200
        data = resp.json()[0]
        assert data["avg_sentiment"] == 0.6
        assert data["std_gpa"] == 0.3
        assert data["match_confidence"] == 95
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Test 10: Active teaching fields in professor response
# ---------------------------------------------------------------------------

def test_professor_response_includes_active_teaching_fields(monkeypatch):
    """Response JSON contains is_active_teacher (bool) and recent_quarters (list of strings)."""
    prof = _make_prof(is_active_teacher=True, recent_quarters=["Fall 2024", "Winter 2024"])
    monkeypatch.setattr("api.routers.courses.get_professors_for_course", lambda db, cid: [prof])
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)
    try:
        resp = client.get("/courses/1/professors")
        assert resp.status_code == 200
        data = resp.json()[0]
        assert data["is_active_teacher"] is True
        assert isinstance(data["recent_quarters"], list)
        assert data["recent_quarters"] == ["Fall 2024", "Winter 2024"]
    finally:
        app.dependency_overrides.clear()


PROFESSOR_RESPONSE_KEYS = {
    "id",
    "name",
    "department",
    "gaucho_score",
    "gpa_factor",
    "quality_factor",
    "difficulty_factor",
    "sentiment_factor",
    "rmp_quality",
    "rmp_difficulty",
    "rmp_would_take_again",
    "rmp_num_ratings",
    "mean_gpa",
    "std_gpa",
    "avg_sentiment",
    "match_confidence",
    "quarters_taught",
    "tags",
    "is_active_teacher",
    "recent_quarters",
    "teaching_next_quarter",
    "scheduled_sections",
    "has_rmp",
}


def test_professor_response_pins_json_shape(monkeypatch):
    """TEST-1: professors payload keeps the contract the SPA type-checks against."""
    prof = _make_prof(is_active_teacher=True, recent_quarters=["Fall 2024"])
    monkeypatch.setattr("api.routers.courses.get_professors_for_course", lambda db, cid: [prof])
    monkeypatch.setattr("api.routers.courses.get_scheduled_sections", lambda *a, **k: {})
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)
    try:
        resp = client.get("/courses/1/professors")
        assert resp.status_code == 200
        assert set(resp.json()[0].keys()) == PROFESSOR_RESPONSE_KEYS
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Test 11: Bayesian small-sample adjustment on quality (BUG-5)
# ---------------------------------------------------------------------------

def test_bayesian_adjustment_shrinks_small_sample_quality(monkeypatch):
    """Identical 5.0 raw quality: the professor with 5 ratings must score below
    the one with 50. Without Bayesian adjustment they tie and tiny samples
    dominate real rankings (BUG-5 / MATH4A Kulick vs Garfield).
    """
    few = _make_prof(
        id=1, name="Few Ratings", mean_gpa=3.5,
        rmp_quality=5.0, rmp_num_ratings=5, rmp_difficulty=3.0, avg_sentiment=0.0,
    )
    many = _make_prof(
        id=2, name="Many Ratings", mean_gpa=3.5,
        rmp_quality=5.0, rmp_num_ratings=50, rmp_difficulty=3.0, avg_sentiment=0.0,
    )
    monkeypatch.setattr(
        "api.routers.courses.get_professors_for_course", lambda db, cid: [few, many]
    )
    monkeypatch.setattr(
        "api.routers.courses.get_scheduled_sections", lambda *a, **k: {}
    )

    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)
    try:
        resp = client.get("/courses/1/professors")
        assert resp.status_code == 200
        by_name = {p["name"]: p for p in resp.json()}
        assert by_name["Few Ratings"]["quality_factor"] < by_name["Many Ratings"]["quality_factor"]
        assert by_name["Few Ratings"]["gaucho_score"] < by_name["Many Ratings"]["gaucho_score"]
        # Raw display value stays unadjusted
        assert by_name["Few Ratings"]["rmp_quality"] == 5.0
        assert by_name["Many Ratings"]["rmp_quality"] == 5.0
    finally:
        app.dependency_overrides.clear()

"""Tests for GET /professors/{id}/grades and GET /professors/{id}/comments.

All 7 behaviours from Plan 02-04, Task 1.
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

def _make_grade_quarter(
    *,
    quarter: str = "Fall 2023",
    avg_gpa: float | None = 3.5,
    a_plus: int = 10,
    a: int = 20,
    a_minus: int = 15,
    b_plus: int = 5,
    b: int = 8,
    b_minus: int = 3,
    c_plus: int = 2,
    c: int = 1,
    c_minus: int = 0,
    d_plus: int = 0,
    d: int = 0,
    d_minus: int = 0,
    f: int = 0,
) -> dict:
    return {
        "quarter": quarter,
        "avg_gpa": avg_gpa,
        "a_plus": a_plus,
        "a": a,
        "a_minus": a_minus,
        "b_plus": b_plus,
        "b": b,
        "b_minus": b_minus,
        "c_plus": c_plus,
        "c": c,
        "c_minus": c_minus,
        "d_plus": d_plus,
        "d": d,
        "d_minus": d_minus,
        "f": f,
    }


def _make_comment(
    *,
    text: str = "Great professor!",
    sentiment_score: float | None = 0.75,
    keywords: list[str] | None = None,
    created_at: str | None = "Jan 2023",
) -> dict:
    return {
        "text": text,
        "sentiment_score": sentiment_score,
        "keywords": keywords or ["helpful", "clear"],
        "created_at": created_at,
    }


# ---------------------------------------------------------------------------
# Test 1: GET /professors/{id}/grades?course_id={cid} → 200 with GradeQuarter list
# ---------------------------------------------------------------------------

def test_get_grades_returns_200_with_grade_quarter_list(monkeypatch):
    grades = [
        _make_grade_quarter(quarter="Fall 2022"),
        _make_grade_quarter(quarter="Winter 2023"),
    ]
    monkeypatch.setattr("api.routers.professors.get_grade_history", lambda db, pid, cid: grades)

    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        client = TestClient(app)
        resp = client.get("/professors/1/grades?course_id=42")

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2
        for item in data:
            assert "quarter" in item
            assert "avg_gpa" in item
            for grade_key in ("a_plus", "a", "a_minus", "b_plus", "b", "b_minus",
                              "c_plus", "c", "c_minus", "d_plus", "d", "d_minus", "f"):
                assert grade_key in item
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Test 2: GET /professors/{id}/grades (no course_id) → 422 (required param)
# ---------------------------------------------------------------------------

def test_get_grades_without_course_id_returns_422():
    client = TestClient(app)
    resp = client.get("/professors/1/grades")
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Test 3: GET /professors/999/grades?course_id=1 → 404 when no data
# ---------------------------------------------------------------------------

def test_get_grades_no_data_returns_404(monkeypatch):
    monkeypatch.setattr("api.routers.professors.get_grade_history", lambda db, pid, cid: [])

    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        client = TestClient(app)
        resp = client.get("/professors/999/grades?course_id=1")

        assert resp.status_code == 404
        assert "999" in resp.json()["detail"]
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Test 4: GET /professors/{id}/comments → 200, default 5 results max
# ---------------------------------------------------------------------------

def test_get_comments_returns_200_with_comment_result_list(monkeypatch):
    comments = [_make_comment(text=f"Comment {i}") for i in range(5)]
    monkeypatch.setattr("api.routers.professors.get_comments_for_professor", lambda db, pid, limit: comments)

    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        client = TestClient(app)
        resp = client.get("/professors/1/comments")

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 5
        for item in data:
            assert "text" in item
            assert "sentiment_score" in item
            assert "keywords" in item
            assert "created_at" in item
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Test 5: GET /professors/{id}/comments?limit=3 → at most 3 results
# ---------------------------------------------------------------------------

def test_get_comments_with_limit_returns_at_most_n_results(monkeypatch):
    # Simulate the query respecting the limit — return exactly 3
    captured = {}
    def mock_query(db, pid, limit=5):
        captured["limit"] = limit
        return [_make_comment(text=f"Comment {i}") for i in range(min(limit, 3))]

    monkeypatch.setattr("api.routers.professors.get_comments_for_professor", mock_query)

    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        client = TestClient(app)
        resp = client.get("/professors/1/comments?limit=3")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) <= 3
        assert captured.get("limit") == 3
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Test 6: GET /professors/999/comments → 404 when no comments
# ---------------------------------------------------------------------------

def test_get_comments_no_data_returns_404(monkeypatch):
    monkeypatch.setattr("api.routers.professors.get_comments_for_professor", lambda db, pid, limit: [])

    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        client = TestClient(app)
        resp = client.get("/professors/999/comments")

        assert resp.status_code == 404
        assert "999" in resp.json()["detail"]
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Test 7: CommentResult.sentiment_score is raw float (VADER [-1,1]) passed through unchanged
# ---------------------------------------------------------------------------

def test_comment_sentiment_score_is_raw_vader_float(monkeypatch):
    """sentiment_score must be passed through as-is — no normalization."""
    raw_score = -0.4767  # typical negative VADER compound score
    comments = [_make_comment(sentiment_score=raw_score)]
    monkeypatch.setattr("api.routers.professors.get_comments_for_professor", lambda db, pid, limit: comments)

    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        client = TestClient(app)
        resp = client.get("/professors/1/comments")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["sentiment_score"] == pytest.approx(raw_score), (
            f"Expected raw VADER score {raw_score}, got {data[0]['sentiment_score']}. "
            "sentiment_score must NOT be normalized — pass it through unchanged."
        )
    finally:
        app.dependency_overrides.clear()

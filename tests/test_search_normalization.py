"""Regression tests for BUG-2 — course search must tolerate whitespace.

Course codes are stored whitespace-free by
scrapers.grades_ingester.normalize_course_code, but students type them the way
the university writes them ("CS 16"). Before this fix every spaced query
returned zero results, including the app's own placeholder examples.
"""
import pytest

from db.models import Course
from dashboard.queries import search_courses
from scrapers.grades_ingester import normalize_course_code


@pytest.fixture
def seeded_courses(db_session):
    db_session.add_all([
        Course(code="CMPSC16", title="Problem Solving I", department="CMPSC"),
        Course(code="MATH4A", title="Linear Algebra", department="MATH"),
        Course(code="PHYS1", title="Basic Physics", department="PHYS"),
    ])
    db_session.flush()
    return db_session


@pytest.mark.parametrize("query", ["CMPSC16", "CMPSC 16", "cmpsc 16", "  CMPSC16  ", "CMPSC  16"])
def test_spaced_and_unspaced_codes_find_same_course(seeded_courses, query):
    """Every spelling of a course code resolves to the same course."""
    results = search_courses(seeded_courses, query)
    assert [r["code"] for r in results] == ["CMPSC16"]


def test_search_matches_ingest_normalization(seeded_courses):
    """Search normalizes queries exactly the way ingest normalizes stored codes."""
    typed = "MATH 4A"
    assert normalize_course_code(typed) == "MATH4A"
    results = search_courses(seeded_courses, typed)
    assert [r["code"] for r in results] == ["MATH4A"]


def test_title_search_preserves_internal_spaces(seeded_courses):
    """Titles contain real spaces, so multi-word title search still works."""
    results = search_courses(seeded_courses, "Problem Solving")
    assert [r["code"] for r in results] == ["CMPSC16"]


def test_empty_query_still_browses_all(seeded_courses):
    """An empty query lists courses rather than returning nothing."""
    assert len(search_courses(seeded_courses, "")) >= 3
    math = search_courses(seeded_courses, "", department="MATH")
    assert all(r["department"] == "MATH" for r in math)


def test_whitespace_only_query_browses_all(seeded_courses):
    """A whitespace-only query behaves like an empty one, not a failed match."""
    assert len(search_courses(seeded_courses, "   ")) >= 3

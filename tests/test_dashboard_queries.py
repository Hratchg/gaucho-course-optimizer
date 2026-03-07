"""Tests for dashboard/queries.py — comments, min_year filter, department filter."""
from datetime import datetime, timezone

from db.models import Professor, Course, GradeDistribution, RmpRating, RmpComment
from dashboard.queries import (
    get_comments_for_professor,
    get_professors_for_course,
    search_courses,
    get_departments,
)


def _seed_professor_with_comments(session):
    """Create a professor with an RMP rating and comments for testing."""
    prof = Professor(name_nexus="Test Prof", department="CMPSC")
    session.add(prof)
    session.flush()

    rating = RmpRating(professor_id=prof.id, overall_quality=4.0, difficulty=2.5, num_ratings=10)
    session.add(rating)
    session.flush()

    comments = [
        RmpComment(
            rmp_rating_id=rating.id,
            comment_text=f"Comment {i}",
            sentiment_score=0.5 - i * 0.2,
            keywords=["good"],
            created_at=datetime(2024, i + 1, 1, tzinfo=timezone.utc),
        )
        for i in range(6)
    ]
    # Add one with NULL created_at
    comments.append(
        RmpComment(
            rmp_rating_id=rating.id,
            comment_text="Old comment",
            sentiment_score=-0.5,
            keywords=["tough"],
            created_at=None,
        )
    )
    session.add_all(comments)
    session.flush()
    return prof


def test_get_comments_returns_most_recent(db_session):
    prof = _seed_professor_with_comments(db_session)
    comments = get_comments_for_professor(db_session, prof.id)

    assert len(comments) == 5
    # Most recent first (June, May, April, ...)
    assert comments[0]["created_at"] == "Jun 2024"
    assert comments[1]["created_at"] == "May 2024"


def test_get_comments_null_date_sorted_last(db_session):
    prof = _seed_professor_with_comments(db_session)
    # Fetch all 7
    comments = get_comments_for_professor(db_session, prof.id, limit=10)

    assert len(comments) == 7
    # NULL created_at should be last
    assert comments[-1]["created_at"] is None
    assert comments[-1]["text"] == "Old comment"


def test_get_comments_empty(db_session):
    prof = Professor(name_nexus="No Comments Prof", department="MATH")
    db_session.add(prof)
    db_session.flush()

    comments = get_comments_for_professor(db_session, prof.id)
    assert comments == []


def test_get_professors_min_year_filter(db_session):
    prof = Professor(name_nexus="Year Prof", department="CMPSC")
    course = Course(code="CMPSC8", title="Intro", department="CMPSC")
    db_session.add_all([prof, course])
    db_session.flush()

    # Add grades across different years
    for year in [2015, 2018, 2022]:
        db_session.add(GradeDistribution(
            professor_id=prof.id, course_id=course.id,
            quarter="Fall", year=year, avg_gpa=3.5,
        ))
    db_session.flush()

    # No filter — all 3 quarters
    result = get_professors_for_course(db_session, course.id)
    assert len(result) == 1
    assert result[0]["quarters_taught"] == 3

    # min_year=2020 — only 2022 quarter
    result = get_professors_for_course(db_session, course.id, min_year=2020)
    assert len(result) == 1
    assert result[0]["quarters_taught"] == 1

    # min_year=2023 — no results
    result = get_professors_for_course(db_session, course.id, min_year=2023)
    assert result == []


def test_search_courses_department_filter(db_session):
    db_session.add_all([
        Course(code="CMPSC8", title="Intro CS", department="CMPSC"),
        Course(code="CMPSC16", title="Problem Solving", department="CMPSC"),
        Course(code="MATH4A", title="Linear Algebra", department="MATH"),
    ])
    db_session.flush()

    # No filter
    all_results = search_courses(db_session, "")
    assert len(all_results) >= 3

    # Filter by CMPSC
    cs_results = search_courses(db_session, "", department="CMPSC")
    assert all(r["department"] == "CMPSC" for r in cs_results)
    assert len(cs_results) >= 2

    # Filter by MATH
    math_results = search_courses(db_session, "", department="MATH")
    assert all(r["department"] == "MATH" for r in math_results)


def test_get_departments(db_session):
    db_session.add_all([
        Course(code="ZTEST1", title="Test 1", department="PHYS"),
        Course(code="ZTEST2", title="Test 2", department="CHEM"),
        Course(code="ZTEST3", title="Test 3", department="PHYS"),
    ])
    db_session.flush()

    depts = get_departments(db_session)
    assert "PHYS" in depts
    assert "CHEM" in depts
    # Should be deduplicated
    assert depts.count("PHYS") == 1

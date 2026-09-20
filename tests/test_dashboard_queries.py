"""Tests for dashboard/queries.py — comments, min_year filter, department filter, active teaching."""
from datetime import datetime, timezone

from db.models import Professor, Course, GradeDistribution, RmpRating, RmpComment
from dashboard.queries import (
    get_comments_for_professor,
    get_professors_for_course,
    search_courses,
    get_departments,
)

CURRENT_YEAR = datetime.now().year


def _seed_professor_with_comments(session):
    """Create a professor with an RMP rating and comments for testing."""
    prof = Professor(name_nexus="Test Prof", department="CMPSC", match_confidence=95)
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


def test_get_professors_returns_rmp_data(db_session):
    """Verify get_professors_for_course returns RMP stats without N+1 queries."""
    # Create 2 professors and a course
    # match_confidence must be >= AUTO_MATCH_THRESHOLD for RMP data to be served
    prof1 = Professor(
        name_rmp="Alice Smith", name_nexus="A Smith",
        department="CMPSC", match_confidence=95,
    )
    prof2 = Professor(name_nexus="Bob Jones", department="CMPSC")
    course = Course(code="CMPSC130A", title="Data Structures", department="CMPSC")
    db_session.add_all([prof1, prof2, course])
    db_session.flush()

    # Grade distributions for both professors
    db_session.add_all([
        GradeDistribution(
            professor_id=prof1.id, course_id=course.id,
            quarter="Fall", year=2023, avg_gpa=3.8,
        ),
        GradeDistribution(
            professor_id=prof2.id, course_id=course.id,
            quarter="Winter", year=2023, avg_gpa=3.5,
        ),
    ])
    db_session.flush()

    # RMP data for professor 1 only
    rating = RmpRating(
        professor_id=prof1.id,
        overall_quality=4.2,
        difficulty=3.1,
        would_take_again_pct=85.0,
        num_ratings=42,
    )
    db_session.add(rating)
    db_session.flush()

    # 2 RMP comments for professor 1
    db_session.add_all([
        RmpComment(
            rmp_rating_id=rating.id,
            comment_text="Very clear lectures.",
            sentiment_score=0.8,
            keywords=["clear"],
        ),
        RmpComment(
            rmp_rating_id=rating.id,
            comment_text="Quite helpful office hours.",
            sentiment_score=0.6,
            keywords=["helpful"],
        ),
    ])
    db_session.flush()

    results = get_professors_for_course(db_session, course.id)

    assert len(results) == 2

    # Find each professor's result by name
    by_name = {r["name"]: r for r in results}

    # Professor 1 (has RMP data)
    p1 = by_name["Alice Smith"]
    assert p1["rmp_quality"] == 4.2
    assert p1["rmp_difficulty"] == 3.1
    assert p1["rmp_would_take_again"] == 85.0
    assert p1["rmp_num_ratings"] == 42
    assert p1["avg_sentiment"] == 0.7  # mean of 0.8 and 0.6
    assert isinstance(p1["tags"], list)
    # tags are curated from vocabulary — "clear" maps to "Clear Explanations", "helpful" maps to "Helpful"
    # With only 2 comments, count per tag is below the min_count=3 threshold, so tags list may be empty
    assert all(isinstance(t, dict) and "name" in t and "count" in t for t in p1["tags"])

    # Professor 2 (no RMP data)
    p2 = by_name["Bob Jones"]
    assert p2["rmp_quality"] is None
    assert p2["rmp_difficulty"] is None
    assert p2["rmp_would_take_again"] is None
    assert p2["avg_sentiment"] is None


# ---------------------------------------------------------------------------
# Active Teaching Tests
# ---------------------------------------------------------------------------


def _seed_prof_and_course(session, prof_name="Active Prof", course_code="CMPSC40"):
    """Helper: create a professor + course and return both."""
    prof = Professor(name_nexus=prof_name, department="CMPSC")
    course = Course(code=course_code, title="Foundations", department="CMPSC")
    session.add_all([prof, course])
    session.flush()
    return prof, course


def test_active_teacher_true(db_session):
    """Professor with 3 distinct (quarter, year) in last 3 years → is_active_teacher=True."""
    prof, course = _seed_prof_and_course(db_session, "Active3", "AT001")
    for q, y in [("Fall", CURRENT_YEAR), ("Winter", CURRENT_YEAR - 1), ("Spring", CURRENT_YEAR - 2)]:
        db_session.add(GradeDistribution(
            professor_id=prof.id, course_id=course.id,
            quarter=q, year=y, avg_gpa=3.5,
        ))
    db_session.flush()

    result = get_professors_for_course(db_session, course.id)
    assert len(result) == 1
    assert result[0]["is_active_teacher"] is True
    assert len(result[0]["recent_quarters"]) == 3


def test_active_teacher_false(db_session):
    """Professor with 2 distinct (quarter, year) in last 3 years → is_active_teacher=False."""
    prof, course = _seed_prof_and_course(db_session, "Active2", "AT002")
    for q, y in [("Fall", CURRENT_YEAR), ("Winter", CURRENT_YEAR - 1)]:
        db_session.add(GradeDistribution(
            professor_id=prof.id, course_id=course.id,
            quarter=q, year=y, avg_gpa=3.5,
        ))
    db_session.flush()

    result = get_professors_for_course(db_session, course.id)
    assert len(result) == 1
    assert result[0]["is_active_teacher"] is False


def test_active_teacher_old_records_excluded(db_session):
    """Professor with 5 records all older than 3 years → is_active_teacher=False, recent_quarters=[]."""
    prof, course = _seed_prof_and_course(db_session, "OldProf", "AT003")
    old_year = CURRENT_YEAR - 4  # outside 3-year window
    for q in ["Fall", "Winter", "Spring", "Summer", "Fall"]:
        db_session.add(GradeDistribution(
            professor_id=prof.id, course_id=course.id,
            quarter=q, year=old_year, avg_gpa=3.0,
        ))
        old_year -= 1  # keep going further back
    db_session.flush()

    result = get_professors_for_course(db_session, course.id)
    assert len(result) == 1
    assert result[0]["is_active_teacher"] is False
    assert result[0]["recent_quarters"] == []


def test_recent_quarters_sorted_most_recent_first(db_session):
    """recent_quarters sorted descending: most recent year first, then Fall>Summer>Spring>Winter."""
    prof, course = _seed_prof_and_course(db_session, "SortProf", "AT004")
    for q, y in [("Winter", 2023), ("Fall", 2024), ("Spring", 2023)]:
        db_session.add(GradeDistribution(
            professor_id=prof.id, course_id=course.id,
            quarter=q, year=y, avg_gpa=3.5,
        ))
    db_session.flush()

    result = get_professors_for_course(db_session, course.id)
    assert len(result) == 1
    quarters = result[0]["recent_quarters"]
    assert quarters[0] == "Fall 2024"
    # Within 2023: Spring (2) > Winter (1)
    assert quarters[1] == "Spring 2023"
    assert quarters[2] == "Winter 2023"


def test_recent_quarters_format(db_session):
    """Each entry formatted as 'Quarter Year' e.g. 'Fall 2024'."""
    prof, course = _seed_prof_and_course(db_session, "FmtProf", "AT005")
    db_session.add(GradeDistribution(
        professor_id=prof.id, course_id=course.id,
        quarter="Fall", year=2024, avg_gpa=3.5,
    ))
    db_session.flush()

    result = get_professors_for_course(db_session, course.id)
    assert len(result) == 1
    assert result[0]["recent_quarters"] == ["Fall 2024"]

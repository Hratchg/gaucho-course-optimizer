"""Regression tests for DATA-1 — weak RMP matches must not be served as fact.

Sub-85% name matches (and rows with no recorded confidence) used to publish
another person's RMP ratings, tags and comments on professor cards. The serve
path now treats those as unmatched.
"""
from datetime import datetime, timezone

from db.models import Professor, Course, GradeDistribution, RmpRating, RmpComment
from dashboard.queries import get_comments_for_professor, get_professors_for_course
from etl.name_matcher import is_confident_match, AUTO_MATCH_THRESHOLD


def _seed_matched_professor(session, *, confidence, name_nexus="WEAK, MATCH", name_rmp="Wrong Person"):
    prof = Professor(
        name_nexus=name_nexus,
        name_rmp=name_rmp,
        department="MATH",
        match_confidence=confidence,
        rmp_id=4242,
    )
    course = Course(code="MATHDATA1", title="Data Quality", department="MATH")
    session.add_all([prof, course])
    session.flush()

    session.add(GradeDistribution(
        professor_id=prof.id, course_id=course.id,
        quarter="Fall", year=2024, avg_gpa=3.8,
    ))
    rating = RmpRating(
        professor_id=prof.id,
        overall_quality=5.0,
        difficulty=1.0,
        would_take_again_pct=100.0,
        num_ratings=5,
    )
    session.add(rating)
    session.flush()
    session.add(RmpComment(
        rmp_rating_id=rating.id,
        comment_text="Amazing lecturer",
        sentiment_score=0.9,
        keywords=["amazing"],
        created_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
    ))
    session.flush()
    return prof, course


def test_is_confident_match_threshold():
    assert AUTO_MATCH_THRESHOLD == 85
    assert is_confident_match(85) is True
    assert is_confident_match(100) is True
    assert is_confident_match(84) is False
    assert is_confident_match(73) is False
    assert is_confident_match(None) is False


def test_low_confidence_rmp_is_stripped_from_professor_listing(db_session):
    """A 73% match must not expose RMP ratings, sentiment or tags."""
    prof, course = _seed_matched_professor(db_session, confidence=73)

    results = get_professors_for_course(db_session, course.id)
    assert len(results) == 1
    row = results[0]

    assert row["rmp_quality"] is None
    assert row["rmp_difficulty"] is None
    assert row["rmp_would_take_again"] is None
    assert row["rmp_num_ratings"] is None
    assert row["avg_sentiment"] is None
    assert row["tags"] == []
    assert row["match_confidence"] is None
    # Display the roster name, not the weakly-matched RMP identity
    assert row["name"] == "WEAK, MATCH"


def test_null_confidence_with_rmp_data_is_stripped(db_session):
    """Legacy rows that never recorded confidence must not leak RMP data."""
    prof, course = _seed_matched_professor(db_session, confidence=None)

    row = get_professors_for_course(db_session, course.id)[0]
    assert row["rmp_quality"] is None
    assert row["name"] == "WEAK, MATCH"


def test_confident_match_still_serves_rmp(db_session):
    prof, course = _seed_matched_professor(
        db_session, confidence=92, name_nexus="STRONG, MATCH", name_rmp="Strong Match",
    )

    row = get_professors_for_course(db_session, course.id)[0]
    assert row["rmp_quality"] == 5.0
    assert row["rmp_num_ratings"] == 5
    assert row["match_confidence"] == 92
    assert row["name"] == "Strong Match"


def test_low_confidence_hides_comments(db_session):
    prof, _ = _seed_matched_professor(db_session, confidence=74)
    assert get_comments_for_professor(db_session, prof.id) == []


def test_confident_match_still_returns_comments(db_session):
    prof, _ = _seed_matched_professor(db_session, confidence=90)
    comments = get_comments_for_professor(db_session, prof.id)
    assert len(comments) == 1
    assert comments[0]["text"] == "Amazing lecturer"

import pytest
from datetime import datetime, timezone

from db.models import Course, GradeDistribution, Professor, RmpComment, RmpRating


@pytest.fixture
def seeded_course(db_session):
    """Seed a Course with one Professor, GradeDistribution, and RmpRating."""
    course = Course(code="CMPSC 32", title="Object Oriented Design", department="CMPSC")
    db_session.add(course)
    db_session.flush()

    prof = Professor(
        name_nexus="Smith, John",
        name_rmp="John Smith",
        rmp_id=12345,
        department="CMPSC",
        match_confidence=95,
    )
    db_session.add(prof)
    db_session.flush()

    grade = GradeDistribution(
        professor_id=prof.id, course_id=course.id,
        quarter="Fall", year=2023, avg_gpa=3.5,
        a_plus=10, a=20, a_minus=5,
        b_plus=3, b=5, b_minus=2,
        c_plus=1, c=1, c_minus=0,
        d_plus=0, d=0, d_minus=0, f=0,
    )
    db_session.add(grade)

    rating = RmpRating(
        professor_id=prof.id, overall_quality=4.2, difficulty=3.1,
        would_take_again_pct=85.0, num_ratings=50,
        fetched_at=datetime.now(timezone.utc),
    )
    db_session.add(rating)
    db_session.flush()

    comment = RmpComment(
        rmp_rating_id=rating.id,
        comment_text="Great professor, very clear.",
        sentiment_score=0.0,   # neutral — sentiment_factor must be 0.5, not 0.0
        keywords=["clear", "helpful"],
        created_at=datetime(2024, 3, 15),
    )
    db_session.add(comment)
    db_session.commit()

    return {"course": course, "professor": prof, "rating": rating}


def test_search_returns_results(client, seeded_course):
    response = client.get("/courses/search?q=CMPSC")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    course_codes = [c["code"] for c in data]
    assert "CMPSC 32" in course_codes


def test_search_rejects_special_chars(client):
    response = client.get("/courses/search?q=physics$123")
    assert response.status_code == 422


def test_search_rejects_long_query(client):
    long_q = "A" * 101
    response = client.get(f"/courses/search?q={long_q}")
    assert response.status_code == 422


def test_professors_returns_ranked_list(client, seeded_course):
    course_id = seeded_course["course"].id
    response = client.get(f"/courses/{course_id}/professors")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    prof = data[0]
    assert "gaucho_score" in prof
    assert "gpa_factor" in prof
    assert "quality_factor" in prof
    assert "difficulty_factor" in prof
    assert "sentiment_factor" in prof


def test_professors_sentiment_normalization(client, seeded_course):
    """Professor with avg_sentiment=0.0 must have sentiment_factor=0.5 (VADER [-1,1] -> [0,1])."""
    course_id = seeded_course["course"].id
    response = client.get(f"/courses/{course_id}/professors")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    # sentiment_score=0.0 is neutral -> normalized to 0.5
    assert data[0]["sentiment_factor"] == pytest.approx(0.5, abs=0.01)


def test_professors_not_found(client):
    response = client.get("/courses/999999/professors")
    assert response.status_code == 404

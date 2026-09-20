import pytest
from datetime import datetime, timezone

from db.models import Course, GradeDistribution, Professor, RmpComment, RmpRating


@pytest.fixture
def seeded_professor(db_session):
    """Seed minimal data for professor endpoint tests."""
    course = Course(code="PHYS 1", title="Intro Physics", department="PHYS")
    db_session.add(course)
    db_session.flush()

    prof = Professor(
        name_nexus="Jones, Alice", name_rmp="Alice Jones",
        rmp_id=99001, department="PHYS", match_confidence=95,
    )
    db_session.add(prof)
    db_session.flush()

    grade = GradeDistribution(
        professor_id=prof.id, course_id=course.id,
        quarter="Winter", year=2024, avg_gpa=3.2,
        a_plus=5, a=15, a_minus=8,
        b_plus=4, b=6, b_minus=2,
        c_plus=1, c=1, c_minus=0,
        d_plus=0, d=0, d_minus=0, f=0,
    )
    db_session.add(grade)

    rating = RmpRating(
        professor_id=prof.id, overall_quality=3.8, difficulty=2.9,
        would_take_again_pct=78.0, num_ratings=25,
        fetched_at=datetime.now(timezone.utc),
    )
    db_session.add(rating)
    db_session.flush()

    for i in range(3):
        comment = RmpComment(
            rmp_rating_id=rating.id,
            comment_text=f"Comment {i}",
            sentiment_score=0.3,
            keywords=["good"],
            created_at=datetime(2024, i + 1, 1),
        )
        db_session.add(comment)

    db_session.commit()
    return {"course": course, "professor": prof}


def test_grades_returns_distribution(client, seeded_professor):
    prof_id = seeded_professor["professor"].id
    course_id = seeded_professor["course"].id
    response = client.get(f"/professors/{prof_id}/grades?course_id={course_id}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    row = data[0]
    assert "quarter" in row
    assert "avg_gpa" in row
    assert "a_plus" in row
    assert "f" in row


def test_grades_requires_course_id(client):
    response = client.get("/professors/1/grades")
    assert response.status_code == 422


def test_grades_not_found(client):
    response = client.get("/professors/999999/grades?course_id=1")
    assert response.status_code == 404


def test_comments_returns_list(client, seeded_professor):
    prof_id = seeded_professor["professor"].id
    response = client.get(f"/professors/{prof_id}/comments")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    comment = data[0]
    assert "text" in comment
    assert "sentiment_score" in comment
    assert "keywords" in comment
    assert "created_at" in comment


def test_comments_limit(client, seeded_professor):
    prof_id = seeded_professor["professor"].id
    response = client.get(f"/professors/{prof_id}/comments?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert 1 <= len(data) <= 2


def test_comments_not_found(client):
    response = client.get("/professors/999999/comments")
    assert response.status_code == 404

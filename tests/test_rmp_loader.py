from db.models import Professor, RmpRating, RmpComment
from scrapers.rmp_loader import load_rmp_teacher_to_db


def test_load_rmp_teacher(db_session):
    teacher = {
        "legacy_id": 9999,
        "first_name": "Alice",
        "last_name": "Wong",
        "department": "Computer Science",
        "avg_rating": 4.5,
        "avg_difficulty": 2.8,
        "would_take_again_pct": 92.0,
        "num_ratings": 30,
        "comments": [
            {"text": "Best professor ever!", "date": "2024-06-01"},
            {"text": "Really helpful in office hours.", "date": "2024-05-15"},
        ],
    }
    load_rmp_teacher_to_db(teacher, db_session)

    prof = db_session.query(Professor).filter_by(rmp_id=9999).first()
    assert prof is not None
    assert prof.name_rmp == "Alice Wong"

    rating = db_session.query(RmpRating).filter_by(professor_id=prof.id).first()
    assert rating.overall_quality == 4.5
    assert rating.num_ratings == 30

    comments = db_session.query(RmpComment).filter_by(rmp_rating_id=rating.id).all()
    assert len(comments) == 2

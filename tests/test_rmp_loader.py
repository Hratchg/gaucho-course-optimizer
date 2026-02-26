from db.models import Professor, RmpRating, RmpComment
from scrapers.rmp_loader import load_rmp_teacher_to_db


def test_load_rmp_teacher_links_nexus_professor(db_session):
    """When nexus_professor_id is provided, link to existing professor instead of creating new."""
    from scrapers.grades_loader import load_grades_to_db

    # First create a Nexus professor via grade loader
    load_grades_to_db([{
        "instructor": "CONRAD, PHILL",
        "course_code": "CMPSC156",
        "quarter": "Fall", "year": 2024,
        "a_plus": 5, "a": 10, "a_minus": 3,
        "b_plus": 2, "b": 1, "b_minus": 0,
        "c_plus": 0, "c": 0, "c_minus": 0,
        "d_plus": 0, "d": 0, "d_minus": 0, "f": 0,
        "avg_gpa": 3.7, "department": "CMPSC",
    }], db_session)

    nexus_prof = db_session.query(Professor).filter_by(name_nexus="CONRAD, PHILL").first()
    assert nexus_prof is not None

    # Now load RMP data linked to this Nexus professor
    teacher = {
        "legacy_id": 7777,
        "first_name": "Phill",
        "last_name": "Conrad",
        "department": "Computer Science",
        "avg_rating": 4.5,
        "avg_difficulty": 2.5,
        "would_take_again_pct": 90.0,
        "num_ratings": 78,
        "comments": [{"text": "Love this class!", "date": "2024-09-01"}],
    }
    load_rmp_teacher_to_db(teacher, db_session, nexus_professor_id=nexus_prof.id, match_confidence=95)

    # Should have updated the existing Nexus professor, not created a new one
    db_session.refresh(nexus_prof)
    assert nexus_prof.rmp_id == 7777
    assert nexus_prof.name_rmp == "Phill Conrad"
    assert nexus_prof.match_confidence == 95

    rating = db_session.query(RmpRating).filter_by(professor_id=nexus_prof.id).first()
    assert rating is not None
    assert rating.overall_quality == 4.5


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

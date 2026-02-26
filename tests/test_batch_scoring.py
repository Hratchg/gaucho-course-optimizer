from db.models import Professor, Course, GradeDistribution, RmpRating, GauchoScore
from etl.scoring import compute_all_scores


def test_compute_all_scores_creates_gaucho_scores(db_session):
    """compute_all_scores creates GauchoScore for matched professors."""
    prof = Professor(name_nexus="SCORE, TEST", rmp_id=1234, match_confidence=95, department="CS")
    db_session.add(prof)
    db_session.flush()

    course = Course(code="CS300", department="CS")
    db_session.add(course)
    db_session.flush()

    db_session.add(GradeDistribution(
        professor_id=prof.id, course_id=course.id,
        quarter="Fall", year=2024, avg_gpa=3.7,
    ))

    db_session.add(RmpRating(
        professor_id=prof.id,
        overall_quality=4.2, difficulty=3.0,
        would_take_again_pct=85.0, num_ratings=40,
    ))
    db_session.commit()

    stats = compute_all_scores(db_session)

    scores = db_session.query(GauchoScore).filter_by(professor_id=prof.id).all()
    assert len(scores) == 1
    assert 0 <= scores[0].score <= 100
    assert scores[0].course_id == course.id
    assert scores[0].weights_used is not None
    assert stats["computed"] >= 1


def test_compute_all_scores_skips_unmatched(db_session):
    """compute_all_scores skips professors without RMP data."""
    prof = Professor(name_nexus="NORP, MATCH", department="MATH")
    db_session.add(prof)
    db_session.flush()

    course = Course(code="MATH500", department="MATH")
    db_session.add(course)
    db_session.flush()

    db_session.add(GradeDistribution(
        professor_id=prof.id, course_id=course.id,
        quarter="Fall", year=2024, avg_gpa=3.0,
    ))
    db_session.commit()

    stats = compute_all_scores(db_session)

    scores = db_session.query(GauchoScore).filter_by(professor_id=prof.id).all()
    assert len(scores) == 0

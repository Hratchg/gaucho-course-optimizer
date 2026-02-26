from datetime import datetime, timezone
from db.models import Professor, Course, GradeDistribution, RmpRating
from scrapers.rmp_loader import get_active_professors, is_stale


def test_get_active_professors_filters_by_year(db_session):
    # Create a professor with a recent grade (2024)
    prof_recent = Professor(name_nexus="RECENT, PROF", department="CS")
    db_session.add(prof_recent)
    db_session.flush()
    course = Course(code="CS101", department="CS")
    db_session.add(course)
    db_session.flush()
    db_session.add(GradeDistribution(
        professor_id=prof_recent.id, course_id=course.id,
        quarter="Fall", year=2024, avg_gpa=3.5,
    ))

    # Create a professor with only old grades (2015)
    prof_old = Professor(name_nexus="OLD, PROF", department="CS")
    db_session.add(prof_old)
    db_session.flush()
    db_session.add(GradeDistribution(
        professor_id=prof_old.id, course_id=course.id,
        quarter="Fall", year=2015, avg_gpa=3.0,
    ))
    db_session.commit()

    active = get_active_professors(db_session, min_year=2023)
    active_ids = [p.id for p in active]
    assert prof_recent.id in active_ids
    assert prof_old.id not in active_ids


def test_is_stale_with_no_rating():
    assert is_stale(None, max_age_days=2) is True


def test_is_stale_with_recent_rating():
    assert is_stale(datetime.now(timezone.utc), max_age_days=2) is False

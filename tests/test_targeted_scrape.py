from unittest.mock import MagicMock, patch
from db.models import Professor, Course, GradeDistribution
from scrapers.targeted_scrape import scrape_active_professors


def test_scrape_matches_and_saves(db_session):
    """Targeted scrape finds RMP match for a Nexus professor and links them."""
    # Set up a Nexus professor
    prof = Professor(name_nexus="CONRAD, PHILL", department="CMPSC")
    db_session.add(prof)
    db_session.flush()
    course = Course(code="CMPSC156", department="CMPSC")
    db_session.add(course)
    db_session.flush()
    db_session.add(GradeDistribution(
        professor_id=prof.id, course_id=course.id,
        quarter="Fall", year=2024, avg_gpa=3.7,
    ))
    db_session.commit()

    # Mock the scraper to return a matching teacher
    mock_scraper = MagicMock()
    mock_scraper.search_teacher_by_name.return_value = [{
        "legacy_id": 7777,
        "first_name": "Phill",
        "last_name": "Conrad",
        "department": "Computer Science",
        "avg_rating": 4.5,
        "avg_difficulty": 2.5,
        "would_take_again_pct": 90.0,
        "num_ratings": 78,
        "comments": [{"text": "Great class!", "date": "2024-09-01"}],
    }]

    stats = scrape_active_professors(db_session, scraper=mock_scraper, min_year=2024, delay=0)

    assert stats["searched"] == 1
    assert stats["matched"] == 1
    assert stats["skipped"] == 0

    db_session.refresh(prof)
    assert prof.rmp_id == 7777
    assert prof.match_confidence >= 85


def test_scrape_skips_low_confidence(db_session):
    """Targeted scrape skips RMP results that don't fuzzy match the Nexus name."""
    prof = Professor(name_nexus="ZHANG, WEI", department="MATH")
    db_session.add(prof)
    db_session.flush()
    course = Course(code="MATH100", department="MATH")
    db_session.add(course)
    db_session.flush()
    db_session.add(GradeDistribution(
        professor_id=prof.id, course_id=course.id,
        quarter="Fall", year=2024, avg_gpa=3.0,
    ))
    db_session.commit()

    mock_scraper = MagicMock()
    mock_scraper.search_teacher_by_name.return_value = [{
        "legacy_id": 8888,
        "first_name": "Robert",
        "last_name": "Johnson",
        "department": "Mathematics",
        "avg_rating": 3.0,
        "avg_difficulty": 3.5,
        "would_take_again_pct": 50.0,
        "num_ratings": 10,
        "comments": [],
    }]

    stats = scrape_active_professors(db_session, scraper=mock_scraper, min_year=2024, delay=0)

    assert stats["matched"] == 0
    assert stats["skipped"] == 1
    assert prof.rmp_id is None


def test_scrape_skips_stale_check(db_session):
    """Targeted scrape skips professors who already have fresh RMP data."""
    from scrapers.rmp_loader import load_rmp_teacher_to_db

    prof = Professor(name_nexus="FRESH, DATA", department="CS")
    db_session.add(prof)
    db_session.flush()
    course = Course(code="CS200", department="CS")
    db_session.add(course)
    db_session.flush()
    db_session.add(GradeDistribution(
        professor_id=prof.id, course_id=course.id,
        quarter="Fall", year=2024, avg_gpa=3.5,
    ))

    # Pre-load RMP data (fresh)
    load_rmp_teacher_to_db({
        "legacy_id": 1111,
        "first_name": "Fresh",
        "last_name": "Data",
        "department": "CS",
        "avg_rating": 4.0,
        "avg_difficulty": 3.0,
        "would_take_again_pct": 80.0,
        "num_ratings": 20,
        "comments": [],
    }, db_session, nexus_professor_id=prof.id, match_confidence=95)

    mock_scraper = MagicMock()
    stats = scrape_active_professors(db_session, scraper=mock_scraper, min_year=2024, delay=0)

    # Should not have called the scraper since data is fresh
    mock_scraper.search_teacher_by_name.assert_not_called()
    assert stats["already_fresh"] >= 1

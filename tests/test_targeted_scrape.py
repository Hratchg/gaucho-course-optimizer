from unittest.mock import MagicMock
from db.models import Professor, Course, GradeDistribution
from scrapers.targeted_scrape import scrape_active_professors
from etl.name_matcher import (
    AUTO_MATCH_THRESHOLD,
    match_confidence as score_fn,
    normalize_nexus_name,
    normalize_rmp_name,
)


def test_scrape_matches_and_saves(db_session):
    """Targeted scrape finds RMP match for a Nexus professor and links them."""
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


def test_scrape_skips_mid_confidence_review_band(db_session):
    """Matches in the old 70-84 'review' band must NOT be written (DATA-1).

    Before the fix, status='review' was only a log label — the row was still
    persisted and served. A 73% match on MATH4A was the top-ranked professor.
    """
    prof = Professor(name_nexus="KULICK, C", department="MATH")
    db_session.add(prof)
    db_session.flush()
    course = Course(code="MATH4A", department="MATH")
    db_session.add(course)
    db_session.flush()
    db_session.add(GradeDistribution(
        professor_id=prof.id, course_id=course.id,
        quarter="Fall", year=2024, avg_gpa=3.5,
    ))
    db_session.commit()

    candidate = {
        "legacy_id": 5555,
        "first_name": "Charles",
        "last_name": "Kulick",
        "department": "Mathematics",
        "avg_rating": 5.0,
        "avg_difficulty": 1.0,
        "would_take_again_pct": 100.0,
        "num_ratings": 5,
        "comments": [],
    }
    # If this pair somehow scores auto-threshold, swap in a weaker name so the
    # assertion exercises the mid-band write gate specifically.
    raw_score = score_fn(
        normalize_nexus_name(prof.name_nexus),
        normalize_rmp_name(f"{candidate['first_name']} {candidate['last_name']}"),
    )
    if raw_score >= AUTO_MATCH_THRESHOLD:
        candidate["first_name"] = "Chuck"
        candidate["last_name"] = "Kulik"
        raw_score = score_fn(
            normalize_nexus_name(prof.name_nexus),
            normalize_rmp_name(f"{candidate['first_name']} {candidate['last_name']}"),
        )
    assert 70 <= raw_score < AUTO_MATCH_THRESHOLD, (
        f"test setup failed to land in the review band, got {raw_score}"
    )

    mock_scraper = MagicMock()
    mock_scraper.search_teacher_by_name.return_value = [candidate]

    stats = scrape_active_professors(db_session, scraper=mock_scraper, min_year=2024, delay=0)

    assert stats["matched"] == 0
    assert stats["skipped"] == 1
    db_session.refresh(prof)
    assert prof.rmp_id is None
    assert prof.match_confidence is None


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

    mock_scraper.search_teacher_by_name.assert_not_called()
    assert stats["already_fresh"] >= 1

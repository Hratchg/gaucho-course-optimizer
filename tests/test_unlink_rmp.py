"""Tests for scripts/unlink_rmp.py — dry-run-first removal of wrong RMP links."""

from unittest.mock import MagicMock

import pytest

from db.models import (
    Course, GauchoScore, GradeDistribution, Professor, RmpComment, RmpRating,
    ScheduledSection,
)
from scrapers.rmp_loader import load_rmp_teacher_to_db
from scrapers.targeted_scrape import scrape_active_professors
from scripts.unlink_rmp import main, parse_targets, unlink_professors


def _teacher(legacy_id, first, last, comments=("Great lectures",)):
    return {
        "legacy_id": legacy_id, "first_name": first, "last_name": last,
        "department": "Computer Science", "avg_rating": 4.2, "avg_difficulty": 3.1,
        "would_take_again_pct": 85.0, "num_ratings": 17,
        "comments": [{"text": c, "date": "2025-01-10 00:00:00 +0000 UTC"} for c in comments],
    }


def _nexus(session, name, dept, course):
    prof = Professor(name_nexus=name, department=dept)
    session.add(prof)
    session.flush()
    session.add(GradeDistribution(
        professor_id=prof.id, course_id=course.id, quarter="Fall", year=2025, avg_gpa=3.4,
    ))
    session.flush()
    return prof


@pytest.fixture
def wrong_link(db_session):
    """YANG M linked to Tao Yang's profile (the production case), YANG T unlinked."""
    course = Course(code="CMPSC 999", department="CMPSC")
    db_session.add(course)
    db_session.flush()
    wrong = _nexus(db_session, "YANG M", "RG", course)
    right = _nexus(db_session, "YANG T", "CMPSC", course)
    load_rmp_teacher_to_db(
        _teacher(845193, "Tao", "Yang", comments=("Hard but fair", "Clear")),
        db_session, nexus_professor_id=wrong.id, match_confidence=90,
    )
    db_session.add(GauchoScore(professor_id=wrong.id, course_id=course.id, score=71.0))
    db_session.add(ScheduledSection(
        professor_id=wrong.id, course_id=course.id, quarter_code="20264",
        enroll_code="54321", instructor_name_raw="YANG M",
    ))
    db_session.commit()
    return wrong, right, course


def _counts(session, prof_id):
    ratings = session.query(RmpRating).filter_by(professor_id=prof_id).count()
    comments = (
        session.query(RmpComment).join(RmpRating, RmpComment.rmp_rating_id == RmpRating.id)
        .filter(RmpRating.professor_id == prof_id).count()
    )
    scores = session.query(GauchoScore).filter_by(professor_id=prof_id).count()
    grades = session.query(GradeDistribution).filter_by(professor_id=prof_id).count()
    return ratings, comments, scores, grades


def test_dry_run_reports_and_changes_nothing(db_session, wrong_link):
    wrong, _, _ = wrong_link

    results = unlink_professors(db_session, [(wrong.id, None)], apply=False)

    assert len(results) == 1
    r = results[0]
    assert r["action"] == "unlink"
    assert r["rmp_id"] == 845193
    assert r["name_rmp"] == "Tao Yang"
    assert (r["ratings"], r["comments"], r["scores"]) == (1, 2, 1)
    db_session.expire_all()
    prof = db_session.get(Professor, wrong.id)
    assert prof.rmp_id == 845193
    assert prof.match_confidence == 90
    assert _counts(db_session, wrong.id) == (1, 2, 1, 1)


def test_apply_clears_link_and_rows_hanging_off_it(db_session, wrong_link):
    wrong, right, _ = wrong_link

    results = unlink_professors(db_session, [(wrong.id, None)], apply=True)

    assert results[0]["action"] == "unlink"
    db_session.expire_all()
    prof = db_session.get(Professor, wrong.id)
    assert prof is not None
    assert (prof.rmp_id, prof.name_rmp, prof.match_confidence) == (None, None, None)
    assert prof.name_nexus == "YANG M"
    assert prof.department == "RG"
    # Ratings, comments and scores go; grade history and sections stay.
    assert _counts(db_session, wrong.id) == (0, 0, 0, 1)
    section = db_session.query(ScheduledSection).filter_by(enroll_code="54321").one()
    assert section.professor_id == wrong.id
    # Nobody else is touched.
    assert _counts(db_session, right.id) == (0, 0, 0, 1)


def test_refresh_relinks_the_profile_to_the_right_professor_after_unlink(db_session, wrong_link):
    wrong, right, _ = wrong_link
    scraper = MagicMock()
    scraper.search_teacher_by_name.return_value = [_teacher(845193, "Tao", "Yang")]

    # Before: the weekly refresh cannot give Tao Yang's profile to YANG T.
    before = scrape_active_professors(db_session, scraper=scraper, min_year=2025, delay=0)
    db_session.expire_all()
    assert db_session.get(Professor, right.id).rmp_id is None
    assert before["errors"] >= 1

    unlink_professors(db_session, [(wrong.id, None)], apply=True)
    after = scrape_active_professors(db_session, scraper=scraper, min_year=2025, delay=0)

    db_session.expire_all()
    assert db_session.get(Professor, right.id).rmp_id == 845193
    assert db_session.get(Professor, wrong.id).rmp_id is None  # guard keeps YANG M off it
    assert after["matched"] == 1


def test_expected_rmp_id_pin_skips_a_link_that_changed(db_session, wrong_link):
    wrong, _, _ = wrong_link

    results = unlink_professors(db_session, [(wrong.id, 1111)], apply=True)

    assert results[0]["action"].startswith("skip")
    assert "845193" in results[0]["action"]
    db_session.expire_all()
    assert db_session.get(Professor, wrong.id).rmp_id == 845193


def test_skips_unknown_unlinked_and_rmp_only_rows(db_session, wrong_link):
    _, right, _ = wrong_link
    rmp_only = Professor(name_rmp="Ian Duncan", rmp_id=2682036, department="Mathematics")
    db_session.add(rmp_only)
    db_session.commit()

    results = unlink_professors(
        db_session, [(right.id, None), (rmp_only.id, None), (987654321, None)], apply=True,
    )

    actions = {r["professor_id"]: r["action"] for r in results}
    assert actions[right.id] == "skip: not linked"
    assert actions[rmp_only.id].startswith("skip: RMP-only row")
    assert actions[987654321] == "skip: no such professor"
    db_session.expire_all()
    assert db_session.get(Professor, rmp_only.id).rmp_id == 2682036


def test_parse_targets_accepts_ids_pins_and_comments(tmp_path):
    ids_file = tmp_path / "ids.txt"
    ids_file.write_text("# clearly wrong\n5194:845193  # YANG M\n\n6197\n")

    assert parse_targets(["5342", "10842:1860302"], str(ids_file)) == [
        (5342, None), (10842, 1860302), (5194, 845193), (6197, None),
    ]


def test_cli_is_dry_run_unless_apply(db_session, wrong_link, capsys):
    wrong, _, _ = wrong_link

    assert main([str(wrong.id)], session=db_session) == 0
    out = capsys.readouterr().out
    assert "DRY RUN" in out
    db_session.expire_all()
    assert db_session.get(Professor, wrong.id).rmp_id == 845193

    assert main([str(wrong.id), "--apply"], session=db_session) == 0
    out = capsys.readouterr().out
    assert "APPLIED" in out
    db_session.expire_all()
    assert db_session.get(Professor, wrong.id).rmp_id is None

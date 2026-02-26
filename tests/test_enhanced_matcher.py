"""Tests for etl/enhanced_matcher.py — multi-pass professor matching."""

import pytest
from db.models import Professor, GradeDistribution, Course, RmpRating
from etl.enhanced_matcher import (
    _get_unmatched_nexus,
    _get_unlinked_rmp,
    _link_professor,
    _pass1_initial_match,
    _pass2_fullname_fuzzy,
    _pass3_dept_disambiguation,
    _pass4_deduplication,
    run_enhanced_matching,
)


def _make_course(session, code="CMPSC 130A"):
    course = Course(code=code, department="CMPSC")
    session.add(course)
    session.flush()
    return course


def _make_nexus_prof(session, name, dept="CMPSC", course=None, year=2024):
    prof = Professor(name_nexus=name, department=dept)
    session.add(prof)
    session.flush()
    if course:
        grade = GradeDistribution(
            professor_id=prof.id, course_id=course.id,
            quarter="Fall", year=year, a=10, avg_gpa=3.5,
        )
        session.add(grade)
        session.flush()
    return prof


def _make_rmp_prof(session, first, last, dept="Computer Science", rmp_id=None):
    prof = Professor(
        name_rmp=f"{first} {last}",
        rmp_id=rmp_id or hash(f"{first}{last}") % 100000,
        department=dept,
    )
    session.add(prof)
    session.flush()
    # Add a rating so relationships work
    rating = RmpRating(
        professor_id=prof.id, overall_quality=4.0,
        difficulty=3.0, num_ratings=10,
    )
    session.add(rating)
    session.flush()
    return prof


class TestGetUnmatched:
    def test_returns_unmatched_with_grades(self, db_session):
        course = _make_course(db_session)
        prof = _make_nexus_prof(db_session, "HUANG L", course=course)
        result = _get_unmatched_nexus(db_session, min_year=2023)
        assert any(p.id == prof.id for p in result)

    def test_excludes_matched(self, db_session):
        course = _make_course(db_session)
        prof = _make_nexus_prof(db_session, "HUANG L", course=course)
        prof.rmp_id = 99999
        db_session.flush()
        result = _get_unmatched_nexus(db_session, min_year=2023)
        assert not any(p.id == prof.id for p in result)


class TestLinkProfessor:
    def test_successful_link(self, db_session):
        course = _make_course(db_session)
        nexus = _make_nexus_prof(db_session, "HUANG L", course=course)
        rmp = _make_rmp_prof(db_session, "Lei", "Huang", rmp_id=12345)
        expected_rmp_id = rmp.rmp_id

        result = _link_professor(db_session, nexus, rmp, 90.0)
        assert result is True
        assert nexus.rmp_id == expected_rmp_id
        assert nexus.name_rmp == "Lei Huang"
        assert nexus.match_confidence == 90.0

    def test_collision_detected(self, db_session):
        course = _make_course(db_session)
        # A professor already linked to rmp_id=12345 (simulates previous match)
        existing = _make_nexus_prof(db_session, "HUANG LEI", course=course)
        existing.rmp_id = 12345
        existing.name_rmp = "Lei Huang"
        db_session.flush()

        # Second nexus prof tries to link to an rmp_prof whose rmp_id is
        # already taken by 'existing'. We pass 'existing' as rmp_prof to
        # trigger the collision guard.
        another = _make_nexus_prof(db_session, "HUANG L", course=course)
        result = _link_professor(db_session, another, existing, 90.0)
        assert result is False
        assert another.rmp_id is None


class TestPass1:
    def test_matches_initial_to_rmp(self, db_session):
        course = _make_course(db_session)
        nexus = _make_nexus_prof(db_session, "HUANG L", course=course)
        rmp = _make_rmp_prof(db_session, "Lei", "Huang")
        expected_rmp_id = rmp.rmp_id

        unmatched = [nexus]
        rmp_profs = [rmp]

        stats = _pass1_initial_match(db_session, unmatched, rmp_profs)
        assert stats["matched"] == 1
        assert nexus.rmp_id == expected_rmp_id

    def test_skips_ambiguous(self, db_session):
        course = _make_course(db_session)
        nexus = _make_nexus_prof(db_session, "HUANG L", course=course)
        rmp1 = _make_rmp_prof(db_session, "Lei", "Huang", rmp_id=111)
        rmp2 = _make_rmp_prof(db_session, "Lin", "Huang", rmp_id=222)

        stats = _pass1_initial_match(db_session, [nexus], [rmp1, rmp2])
        assert stats["ambiguous"] == 1
        assert nexus.rmp_id is None


class TestPass2:
    def test_fuzzy_matches_full_name(self, db_session):
        course = _make_course(db_session)
        nexus = _make_nexus_prof(db_session, "SMITH, JOHN", course=course)
        rmp = _make_rmp_prof(db_session, "John", "Smith")

        stats = _pass2_fullname_fuzzy(db_session, min_year=2023)
        assert stats["matched"] == 1
        assert nexus.rmp_id is not None


class TestPass4:
    def test_merges_duplicates(self, db_session):
        course = _make_course(db_session)
        abbr = _make_nexus_prof(db_session, "CHANG S", dept="CMPSC", course=course)
        full = _make_nexus_prof(db_session, "CHANG SHIYU", dept="CMPSC", course=course)
        abbr_id = abbr.id
        full_id = full.id

        stats = _pass4_deduplication(db_session, min_year=2023)
        assert stats["merged"] == 1
        # Abbreviated professor should be deleted
        assert db_session.get(Professor, abbr_id) is None
        # Full-name professor should have the grades
        remaining = db_session.get(Professor, full_id)
        assert remaining is not None

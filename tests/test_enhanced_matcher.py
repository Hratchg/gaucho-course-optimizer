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
        assert nexus.match_confidence == 90.0

    def test_skips_ambiguous(self, db_session):
        course = _make_course(db_session)
        nexus = _make_nexus_prof(db_session, "HUANG L", course=course)
        rmp1 = _make_rmp_prof(db_session, "Lei", "Huang", rmp_id=111)
        rmp2 = _make_rmp_prof(db_session, "Lin", "Huang", rmp_id=222)

        stats = _pass1_initial_match(db_session, [nexus], [rmp1, rmp2])
        assert stats["ambiguous"] == 1
        assert nexus.rmp_id is None

    def test_skips_department_mismatch(self, db_session):
        """Initial-only links across departments used to write at confidence 75
        (DATA-1 / BUG-9). Surname+initial alone is not enough when depts disagree.
        """
        course = _make_course(db_session)
        nexus = _make_nexus_prof(db_session, "HUANG L", dept="CMPSC", course=course)
        # Same last name + initial, but History instead of Computer Science
        rmp = _make_rmp_prof(db_session, "Lei", "Huang", dept="History", rmp_id=333)

        stats = _pass1_initial_match(db_session, [nexus], [rmp])
        assert stats["matched"] == 0
        assert stats["dept_mismatch"] == 1
        assert nexus.rmp_id is None
        assert nexus.match_confidence is None

    def test_does_not_reuse_consumed_rmp_candidate(self, db_session):
        """BUG-8: after linking, the consumed RMP row must leave the candidate pool.

        Two abbreviated Nexus professors share a surname + initial. Without
        pruning, the second is handed the same (now-deleted) RMP object.
        """
        course = _make_course(db_session)
        first = _make_nexus_prof(db_session, "HUANG L", course=course)
        second = _make_nexus_prof(db_session, "HUANG L", course=course)
        rmp = _make_rmp_prof(db_session, "Lei", "Huang", rmp_id=444)
        expected_rmp_id = rmp.rmp_id

        stats = _pass1_initial_match(db_session, [first, second], [rmp])
        assert stats["matched"] == 1
        assert stats["no_candidate"] == 1
        linked = [p for p in (first, second) if p.rmp_id == expected_rmp_id]
        unmatched = [p for p in (first, second) if p.rmp_id is None]
        assert len(linked) == 1
        assert len(unmatched) == 1


class TestPass2:
    def test_fuzzy_matches_full_name(self, db_session):
        course = _make_course(db_session)
        nexus = _make_nexus_prof(db_session, "SMITH, JOHN", course=course)
        rmp = _make_rmp_prof(db_session, "John", "Smith")

        stats = _pass2_fullname_fuzzy(db_session, min_year=2023)
        assert stats["matched"] == 1
        assert nexus.rmp_id is not None

    def test_truncated_hyphenated_surname(self, db_session):
        course = _make_course(db_session, code="SPANTRUNC")
        nexus = _make_nexus_prof(db_session, "CASTELLA-CABE", dept="SPAN", course=course)
        rmp = _make_rmp_prof(db_session, "Ana", "Castellanos Cabrera", dept="Spanish")
        nexus.department = "SPAN"
        db_session.flush()

        stats = _pass2_fullname_fuzzy(db_session, min_year=2023)
        assert stats["matched"] == 1
        db_session.refresh(nexus)
        assert nexus.rmp_id is not None
        assert nexus.name_rmp == "Ana Castellanos Cabrera"
        assert nexus.match_confidence >= 85


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

    def test_skips_ambiguous_abbreviated_name(self, db_session):
        """BUG-10: SMITH J matching both JOHN and JANE must not merge by iteration order."""
        course = _make_course(db_session, code="CMPSCBUG10")
        abbr = _make_nexus_prof(db_session, "SMITH J", dept="CMPSC", course=course)
        john = _make_nexus_prof(db_session, "SMITH JOHN", dept="CMPSC", course=course)
        jane = _make_nexus_prof(db_session, "SMITH JANE", dept="CMPSC", course=course)
        abbr_id, john_id, jane_id = abbr.id, john.id, jane.id

        stats = _pass4_deduplication(db_session, min_year=2023)
        assert stats["merged"] == 0
        assert stats["skipped_ambiguous"] == 1
        assert db_session.get(Professor, abbr_id) is not None
        assert db_session.get(Professor, john_id) is not None
        assert db_session.get(Professor, jane_id) is not None


class TestConsumedCandidatesAcrossPasses:
    def test_run_all_passes_does_not_hand_deleted_rmp_to_second_abbrev(self, db_session):
        """BUG-8 e2e: two abbreviated Nexus rows share a surname/initial.

        Only one RMP candidate exists. The second Nexus professor must stay
        unmatched — not be handed the row pass 1 already deleted.
        """
        course = _make_course(db_session, code="CMPSCBUG8")
        first = _make_nexus_prof(db_session, "HUANG L", course=course)
        second = _make_nexus_prof(db_session, "HUANG L", course=course)
        rmp = _make_rmp_prof(db_session, "Lei", "Huang", rmp_id=555)
        expected_rmp_id = rmp.rmp_id

        result = run_enhanced_matching(db_session, min_year=2023)
        assert result["pass1"]["matched"] == 1
        assert result["pass1"]["no_candidate"] == 1

        db_session.refresh(first)
        db_session.refresh(second)
        linked = [p for p in (first, second) if p.rmp_id == expected_rmp_id]
        unmatched = [p for p in (first, second) if p.rmp_id is None]
        assert len(linked) == 1
        assert len(unmatched) == 1
        # The RMP-only row is gone; the consumed id must not reappear on both.
        assert db_session.query(Professor).filter_by(rmp_id=expected_rmp_id).count() == 1

    def test_pass3_does_not_reuse_consumed_rmp_candidate(self, db_session):
        """Pass 3 also built rmp_by_last up front and never pruned it."""
        course = _make_course(db_session, code="CMPSCBUG8P3")
        first = _make_nexus_prof(db_session, "HUANG L", course=course)
        second = _make_nexus_prof(db_session, "HUANG L", course=course)
        lei = _make_rmp_prof(db_session, "Lei", "Huang", dept="Computer Science", rmp_id=701)
        lin = _make_rmp_prof(db_session, "Lin", "Huang", dept="History", rmp_id=702)
        expected = lei.rmp_id

        # Pass 1 sees two last+initial candidates → ambiguous, no link.
        p1 = _pass1_initial_match(db_session, [first, second], [lei, lin])
        assert p1["matched"] == 0
        assert p1["ambiguous"] == 2

        p3 = _pass3_dept_disambiguation(db_session, min_year=2023)
        assert p3["matched"] == 1
        db_session.refresh(first)
        db_session.refresh(second)
        linked = [p for p in (first, second) if p.rmp_id == expected]
        unmatched = [p for p in (first, second) if p.rmp_id is None]
        assert len(linked) == 1
        assert len(unmatched) == 1

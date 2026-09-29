"""Tests for etl/enhanced_matcher.py — multi-pass professor matching."""

import logging

import pytest
from db.models import (
    Professor, GradeDistribution, Course, RmpRating, RmpComment, GauchoScore,
    ScheduledSection,
)
import etl.enhanced_matcher as enhanced_matcher
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

    def test_moves_sections_and_scores_off_the_deleted_rmp_row(self, db_session):
        """The schedule sync can attach sections to an RMP-only row by name_rmp.
        Linking deletes that row, so its sections (and scores) must move to the
        Nexus professor instead of being left with no professor (WANG E ->
        "Eric Wang" stranded 15 sections)."""
        course = _make_course(db_session)
        other_course = _make_course(db_session, code="CMPSC 130B")
        nexus = _make_nexus_prof(db_session, "WANG E", course=course)
        rmp = _make_rmp_prof(db_session, "Eric", "Wang", rmp_id=5150)
        rmp_row_id = rmp.id
        for code in ("11111", "22222"):
            db_session.add(ScheduledSection(
                professor_id=rmp.id, course_id=course.id, quarter_code="20264",
                enroll_code=code, instructor_name_raw="WANG E",
            ))
        # Same course on both rows collides on uq_gaucho_score_pair: keep the
        # Nexus row's score. A course only the RMP row has moves across.
        db_session.add(GauchoScore(professor_id=nexus.id, course_id=course.id, score=60.0))
        db_session.add(GauchoScore(professor_id=rmp.id, course_id=course.id, score=99.0))
        db_session.add(GauchoScore(professor_id=rmp.id, course_id=other_course.id, score=70.0))
        db_session.flush()

        assert _link_professor(db_session, nexus, rmp, 90.0) is True

        assert db_session.get(Professor, rmp_row_id) is None
        sections = db_session.query(ScheduledSection).filter(
            ScheduledSection.enroll_code.in_(["11111", "22222"])
        ).all()
        assert [s.professor_id for s in sections] == [nexus.id, nexus.id]
        scores = {
            s.course_id: s.score
            for s in db_session.query(GauchoScore).filter_by(professor_id=nexus.id)
        }
        assert scores == {course.id: 60.0, other_course.id: 70.0}
        assert db_session.query(GauchoScore).filter_by(professor_id=rmp_row_id).count() == 0


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

    def test_rejects_rmp_first_name_that_conflicts_with_nexus_initials(self, db_session):
        """Multi-initial names skip passes 1 and 3 and land here; the fuzzy
        score alone links BERGSTROM R E to "Ted Bergstrom" at 85."""
        course = _make_course(db_session, code="ECON1")
        nexus = _make_nexus_prof(db_session, "BERGSTROM R E", dept="ECON", course=course)
        _make_rmp_prof(db_session, "Ted", "Bergstrom", dept="Economics", rmp_id=110288)

        stats = _pass2_fullname_fuzzy(db_session, min_year=2023)
        assert stats["matched"] == 0
        assert nexus.rmp_id is None

    def test_keeps_middle_initial_match(self, db_session):
        course = _make_course(db_session, code="ENV3")
        nexus = _make_nexus_prof(db_session, "ZIMMERMAN E D", dept="ENV", course=course)
        _make_rmp_prof(db_session, "Don", "Zimmerman", dept="Environmental Studies", rmp_id=2811373)

        stats = _pass2_fullname_fuzzy(db_session, min_year=2023)
        assert stats["matched"] == 1
        db_session.refresh(nexus)
        assert nexus.rmp_id == 2811373


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



def _add_grade(session, prof, course, quarter="Fall", year=2024, a=10, b=0, avg_gpa=3.5):
    grade = GradeDistribution(
        professor_id=prof.id, course_id=course.id,
        quarter=quarter, year=year, a=a, b=b, avg_gpa=avg_gpa,
    )
    session.add(grade)
    session.flush()
    return grade


def _add_score(session, prof, course, score=70.0):
    row = GauchoScore(professor_id=prof.id, course_id=course.id, score=score, weights_used={})
    session.add(row)
    session.flush()
    return row


def _add_section(session, prof, course, enroll_code, quarter_code="20264"):
    section = ScheduledSection(
        professor_id=prof.id, course_id=course.id, quarter_code=quarter_code,
        enroll_code=enroll_code, instructor_name_raw=prof.name_nexus,
    )
    session.add(section)
    session.flush()
    return section


def _link_rmp(session, prof, rmp_id, name_rmp):
    """Give a Nexus professor an RMP link with one rating and one comment."""
    prof.rmp_id = rmp_id
    prof.name_rmp = name_rmp
    prof.match_confidence = 90.0
    rating = RmpRating(professor_id=prof.id, overall_quality=4.0, difficulty=3.0, num_ratings=10)
    session.add(rating)
    session.flush()
    comment = RmpComment(rmp_rating_id=rating.id, comment_text="great")
    session.add(comment)
    session.flush()
    return rating, comment


def _grade_rows(session, prof_id):
    return (
        session.query(GradeDistribution)
        .filter_by(professor_id=prof_id)
        .order_by(GradeDistribution.id)
        .all()
    )


class TestPass4MergesEveryReference:
    """Pass 4 deletes a professor row, so every row pointing at it must move first."""

    def test_scores_on_both_sides_for_same_course(self, db_session):
        """uq_gaucho_score_pair: the loser's score for a course the survivor
        already has is dropped (scores are derived); its other scores move."""
        shared = _make_course(db_session, code="P4SCORE1")
        only_abbr = _make_course(db_session, code="P4SCORE2")
        abbr = _make_nexus_prof(db_session, "HUANG L", course=shared, year=2023)
        full = _make_nexus_prof(db_session, "HUANG LEI", course=shared, year=2024)
        _add_grade(db_session, abbr, only_abbr)
        _link_rmp(db_session, abbr, 9101, "Lei Huang")
        survivor_score = _add_score(db_session, full, shared, score=80.0)
        _add_score(db_session, abbr, shared, score=60.0)
        moved_score = _add_score(db_session, abbr, only_abbr, score=65.0)
        abbr_id, full_id = abbr.id, full.id
        survivor_score_id, moved_score_id = survivor_score.id, moved_score.id

        stats = _pass4_deduplication(db_session, min_year=2023)

        assert stats["merged"] == 1
        db_session.expire_all()
        assert db_session.get(Professor, abbr_id) is None
        scores = {
            s.course_id: (s.id, s.score)
            for s in db_session.query(GauchoScore).filter_by(professor_id=full_id)
        }
        assert scores == {
            shared.id: (survivor_score_id, 80.0),
            only_abbr.id: (moved_score_id, 65.0),
        }
        assert db_session.query(GauchoScore).filter_by(professor_id=abbr_id).count() == 0

    def test_rmp_link_ratings_and_comments_move_to_survivor(self, db_session):
        course = _make_course(db_session, code="P4RMP")
        abbr = _make_nexus_prof(db_session, "HUANG L", course=course, year=2023)
        full = _make_nexus_prof(db_session, "HUANG LEI", course=course, year=2024)
        rating, comment = _link_rmp(db_session, abbr, 9102, "Lei Huang")
        abbr_id, full_id, rating_id, comment_id = abbr.id, full.id, rating.id, comment.id

        stats = _pass4_deduplication(db_session, min_year=2023)

        assert stats["merged"] == 1
        db_session.expire_all()
        survivor = db_session.get(Professor, full_id)
        assert (survivor.rmp_id, survivor.name_rmp, survivor.match_confidence) == (
            9102, "Lei Huang", 90.0,
        )
        assert db_session.get(RmpRating, rating_id).professor_id == full_id
        assert db_session.get(RmpComment, comment_id).rmp_rating_id == rating_id
        assert db_session.get(Professor, abbr_id) is None

    def test_both_linked_to_different_rmp_profiles_is_not_merged(self, db_session):
        """Two RMP profiles means two people (or an RMP duplicate): leave it for a human."""
        course = _make_course(db_session, code="P4RMPBOTH")
        abbr = _make_nexus_prof(db_session, "HUANG L", course=course, year=2023)
        full = _make_nexus_prof(db_session, "HUANG LEI", course=course, year=2024)
        _link_rmp(db_session, abbr, 9103, "Lin Huang")
        _link_rmp(db_session, full, 9104, "Lei Huang")
        _add_score(db_session, abbr, course)
        _add_score(db_session, full, course)
        abbr_id, full_id = abbr.id, full.id

        stats = _pass4_deduplication(db_session, min_year=2023)

        assert stats["merged"] == 0
        assert stats["skipped_rmp_conflict"] == 1
        db_session.expire_all()
        assert db_session.get(Professor, abbr_id).rmp_id == 9103
        assert db_session.get(Professor, full_id).rmp_id == 9104
        assert len(_grade_rows(db_session, abbr_id)) == 1
        assert db_session.query(GauchoScore).filter_by(professor_id=abbr_id).count() == 1

    def test_sections_move_to_survivor(self, db_session):
        course = _make_course(db_session, code="P4SECT")
        abbr = _make_nexus_prof(db_session, "CHANG S", course=course, year=2023)
        full = _make_nexus_prof(db_session, "CHANG SHIYU", course=course, year=2024)
        s1 = _add_section(db_session, abbr, course, "11111")
        s2 = _add_section(db_session, abbr, course, "22222")
        s3 = _add_section(db_session, full, course, "33333")
        section_ids = [s1.id, s2.id, s3.id]
        abbr_id, full_id = abbr.id, full.id

        stats = _pass4_deduplication(db_session, min_year=2023)

        assert stats["merged"] == 1
        db_session.expire_all()
        owners = [db_session.get(ScheduledSection, sid).professor_id for sid in section_ids]
        assert owners == [full_id, full_id, full_id]
        # Raw instructor name is kept for debugging.
        assert db_session.get(ScheduledSection, section_ids[0]).instructor_name_raw == "CHANG S"
        assert db_session.get(Professor, abbr_id) is None

    def test_grades_without_key_collision_all_move(self, db_session):
        course = _make_course(db_session, code="P4GRADES")
        abbr = _make_nexus_prof(db_session, "CHANG S", course=course, year=2022)
        full = _make_nexus_prof(db_session, "CHANG SHIYU", course=course, year=2024)
        _add_grade(db_session, abbr, course, quarter="Spring", year=2023)
        abbr_ids = [g.id for g in _grade_rows(db_session, abbr.id)]
        full_ids = [g.id for g in _grade_rows(db_session, full.id)]
        abbr_id, full_id = abbr.id, full.id

        _pass4_deduplication(db_session, min_year=2023)

        db_session.expire_all()
        assert sorted(g.id for g in _grade_rows(db_session, full_id)) == sorted(abbr_ids + full_ids)
        assert _grade_rows(db_session, abbr_id) == []

    def test_identical_grade_key_is_deduplicated(self, db_session):
        """Same (course, quarter, year) with the same numbers is one record loaded
        twice under two spellings: keep the survivor's row, drop the copy."""
        course = _make_course(db_session, code="P4DUPKEY")
        abbr = _make_nexus_prof(db_session, "CHANG S", course=course, year=2024)
        full = _make_nexus_prof(db_session, "CHANG SHIYU", course=course, year=2024)
        _add_grade(db_session, abbr, course, quarter="Winter", year=2023)
        survivor_row_id = _grade_rows(db_session, full.id)[0].id
        moved_row_id = _grade_rows(db_session, abbr.id)[1].id
        total_before = db_session.query(GradeDistribution).count()
        abbr_id, full_id = abbr.id, full.id

        stats = _pass4_deduplication(db_session, min_year=2023)

        assert stats["merged"] == 1
        db_session.expire_all()
        rows = _grade_rows(db_session, full_id)
        assert sorted(g.id for g in rows) == sorted([survivor_row_id, moved_row_id])
        keys = [(g.course_id, g.quarter, g.year) for g in rows]
        assert len(keys) == len(set(keys))
        assert db_session.query(GradeDistribution).count() == total_before - 1
        assert db_session.get(Professor, abbr_id) is None

    def test_conflicting_grade_key_skips_the_merge(self, db_session):
        """Same key with different numbers: two instructors taught the course that
        quarter, or the data disagrees. Neither is safe to fold together."""
        course = _make_course(db_session, code="P4CONFLICT")
        abbr = _make_nexus_prof(db_session, "CHANG S", dept="CMPSC")
        full = _make_nexus_prof(db_session, "CHANG SHIYU", dept="CMPSC")
        _add_grade(db_session, abbr, course, a=10, avg_gpa=3.5)
        _add_grade(db_session, full, course, a=12, b=4, avg_gpa=3.4)
        _add_section(db_session, abbr, course, "44444")
        abbr_id, full_id = abbr.id, full.id

        stats = _pass4_deduplication(db_session, min_year=2023)

        assert stats["merged"] == 0
        assert stats["skipped_grade_conflict"] == 1
        db_session.expire_all()
        assert db_session.get(Professor, abbr_id) is not None
        assert [g.a for g in _grade_rows(db_session, abbr_id)] == [10]
        assert [g.a for g in _grade_rows(db_session, full_id)] == [12]
        assert db_session.query(ScheduledSection).filter_by(professor_id=abbr_id).count() == 1


class TestPass4DryRun:
    def _setup(self, db_session):
        course = _make_course(db_session, code="P4DRY")
        other = _make_course(db_session, code="P4DRY2")
        abbr = _make_nexus_prof(db_session, "HUANG L", course=course, year=2023)
        full = _make_nexus_prof(db_session, "HUANG LEI", course=course, year=2024)
        rating, _comment = _link_rmp(db_session, abbr, 9201, "Lei Huang")
        _add_score(db_session, abbr, course)
        _add_score(db_session, abbr, other)
        _add_score(db_session, full, course)
        _add_section(db_session, abbr, course, "55555")
        db_session.commit()
        return abbr.id, full.id, rating.id

    def _assert_untouched(self, db_session, abbr_id, full_id, rating_id):
        assert not db_session.new and not db_session.dirty and not db_session.deleted
        db_session.expire_all()
        abbr = db_session.get(Professor, abbr_id)
        full = db_session.get(Professor, full_id)
        assert abbr is not None
        assert (abbr.rmp_id, abbr.name_rmp) == (9201, "Lei Huang")
        assert (full.rmp_id, full.name_rmp, full.match_confidence) == (None, None, None)
        assert db_session.get(RmpRating, rating_id).professor_id == abbr_id
        assert len(_grade_rows(db_session, abbr_id)) == 1
        assert db_session.query(GauchoScore).filter_by(professor_id=abbr_id).count() == 2
        assert db_session.query(ScheduledSection).filter_by(professor_id=abbr_id).count() == 1

    def test_pass4_dry_run_makes_no_changes(self, db_session):
        abbr_id, full_id, rating_id = self._setup(db_session)

        stats = _pass4_deduplication(db_session, min_year=2023, dry_run=True)

        assert stats["merged"] == 1  # reported as "would merge"
        self._assert_untouched(db_session, abbr_id, full_id, rating_id)

    def test_run_enhanced_matching_dry_run_makes_no_changes(self, db_session):
        abbr_id, full_id, rating_id = self._setup(db_session)

        result = run_enhanced_matching(db_session, min_year=2023, dry_run=True)

        assert result["total_merges"] == 1
        self._assert_untouched(db_session, abbr_id, full_id, rating_id)


class TestPass4Atomicity:
    def test_failed_merge_leaves_that_pair_untouched_and_others_merge(
        self, db_session, monkeypatch, caplog,
    ):
        course = _make_course(db_session, code="P4ATOMIC")
        bad_abbr = _make_nexus_prof(db_session, "CHANG S", course=course, year=2022)
        bad_full = _make_nexus_prof(db_session, "CHANG SHIYU", course=course, year=2024)
        _add_section(db_session, bad_abbr, course, "66666")
        good_abbr = _make_nexus_prof(db_session, "WONG K", course=course, year=2022)
        good_full = _make_nexus_prof(db_session, "WONG KAREN", course=course, year=2024)
        bad_abbr_id, bad_full_id = bad_abbr.id, bad_full.id
        good_abbr_id, good_full_id = good_abbr.id, good_full.id

        # Fail after the grades have already been moved for the first pair.
        real_move_sections = enhanced_matcher._move_sections

        def flaky_move_sections(session, loser_id, survivor_id):
            if loser_id == bad_abbr_id:
                raise RuntimeError("boom")
            return real_move_sections(session, loser_id, survivor_id)

        monkeypatch.setattr(enhanced_matcher, "_move_sections", flaky_move_sections)

        with caplog.at_level(logging.INFO, logger="etl.enhanced_matcher"):
            stats = _pass4_deduplication(db_session, min_year=2023)

        assert stats["merged"] == 1
        assert stats["failed"] == 1
        db_session.expire_all()
        # The failed pair is exactly as it was: grades not half-moved.
        assert db_session.get(Professor, bad_abbr_id) is not None
        assert [g.year for g in _grade_rows(db_session, bad_abbr_id)] == [2022]
        assert [g.year for g in _grade_rows(db_session, bad_full_id)] == [2024]
        assert db_session.query(ScheduledSection).filter_by(professor_id=bad_abbr_id).count() == 1
        # The other pair merged.
        assert db_session.get(Professor, good_abbr_id) is None
        assert len(_grade_rows(db_session, good_full_id)) == 2
        # Audit trail names both ids.
        merged_logs = [r.getMessage() for r in caplog.records if "merged professor" in r.getMessage()]
        assert any(f"id={good_abbr_id}" in m and f"id={good_full_id}" in m for m in merged_logs)


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


class TestUnattendedRun:
    """The weekly refresh runs matching with nobody reviewing the result."""

    def test_merge_duplicates_false_skips_pass4(self, db_session):
        """Pass 4 deletes professor rows, so unattended runs must leave it out."""
        course = _make_course(db_session, code="CMPSCNOMERGE")
        abbr = _make_nexus_prof(db_session, "CHANG S", dept="CMPSC", course=course)
        full = _make_nexus_prof(db_session, "CHANG SHIYU", dept="CMPSC", course=course)
        abbr_id, full_id = abbr.id, full.id

        result = run_enhanced_matching(db_session, min_year=2023, merge_duplicates=False)

        assert result["pass4"] == {"merged": 0, "skipped_ambiguous": 0, "skipped": True}
        assert result["total_merges"] == 0
        assert db_session.get(Professor, abbr_id) is not None
        assert db_session.get(Professor, full_id) is not None

    def test_links_still_happen_without_merging(self, db_session):
        course = _make_course(db_session, code="CMPSCLINKONLY")
        nexus = _make_nexus_prof(db_session, "SMITH, JOHN", course=course)
        _make_rmp_prof(db_session, "John", "Smith", rmp_id=8801)

        result = run_enhanced_matching(db_session, min_year=2023, merge_duplicates=False)

        assert result["total_new_matches"] == 1
        db_session.refresh(nexus)
        assert nexus.rmp_id == 8801

    def test_second_run_changes_nothing(self, db_session):
        """Already-linked rows are filtered out, so a rerun is a no-op."""
        course = _make_course(db_session, code="CMPSCRERUN")
        nexus = _make_nexus_prof(db_session, "SMITH, JOHN", course=course)
        _make_rmp_prof(db_session, "John", "Smith", rmp_id=8802)

        first = run_enhanced_matching(db_session, min_year=2023, merge_duplicates=False)
        assert first["total_new_matches"] == 1
        db_session.refresh(nexus)
        linked = (nexus.rmp_id, nexus.name_rmp, nexus.match_confidence)

        second = run_enhanced_matching(db_session, min_year=2023, merge_duplicates=False)
        assert second["total_new_matches"] == 0
        db_session.refresh(nexus)
        assert (nexus.rmp_id, nexus.name_rmp, nexus.match_confidence) == linked
        assert db_session.query(Professor).filter_by(rmp_id=8802).count() == 1

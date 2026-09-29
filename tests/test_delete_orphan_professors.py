"""Tests for scripts/delete_orphan_professors.py."""

from unittest.mock import MagicMock

import pytest
from sqlalchemy import text

from db.models import (
    Course,
    GauchoScore,
    GradeDistribution,
    Professor,
    RmpRating,
    ScheduledSection,
)
from scripts.delete_orphan_professors import (
    check_schema,
    collect_stats,
    delete_orphans,
    run,
)
from ucsb_api.name_matcher import match_instructor_to_professor, parse_ucsb_instructor
from ucsb_api.schedule_sync import _build_professor_lookup, sync_department_sections


def _prof(session, name_nexus, **kw):
    prof = Professor(name_nexus=name_nexus, department=kw.pop("department", "HIST"), **kw)
    session.add(prof)
    session.flush()
    return prof


def _ids(session):
    return {p.id for p in session.query(Professor.id)}


@pytest.fixture
def course(db_session):
    c = Course(code="HIST4A", title="World History", department="HIST")
    db_session.add(c)
    db_session.flush()
    return c


@pytest.fixture
def seeded(db_session, course):
    """A table shaped like production: one name with many nightly duplicates."""
    rows = {}
    # Oldest row of the name is the keeper, the rest are sync leftovers.
    rows["keeper"] = _prof(db_session, "ESCALANTE N")
    rows["dupes"] = [_prof(db_session, "ESCALANTE N") for _ in range(5)]

    # Each kind of reference keeps an otherwise identical duplicate alive.
    rows["graded"] = _prof(db_session, "ESCALANTE N")
    db_session.add(GradeDistribution(professor_id=rows["graded"].id, course_id=course.id,
                                     quarter="Fall", year=2024, avg_gpa=3.1))
    rows["rated"] = _prof(db_session, "ESCALANTE N")
    db_session.add(RmpRating(professor_id=rows["rated"].id, overall_quality=4.0,
                             difficulty=2.0, num_ratings=3))
    rows["scored"] = _prof(db_session, "ESCALANTE N")
    db_session.add(GauchoScore(professor_id=rows["scored"].id, course_id=course.id, score=70))
    rows["scheduled"] = _prof(db_session, "ESCALANTE N")
    db_session.add(ScheduledSection(professor_id=rows["scheduled"].id, course_id=course.id,
                                    quarter_code="20254", enroll_code="11111"))
    rows["rmp_id"] = _prof(db_session, "ESCALANTE N", rmp_id=424242)
    rows["name_rmp"] = _prof(db_session, "ESCALANTE N", name_rmp="Nora Escalante")

    # RMP-only row (no Nexus name) with ratings is not an orphan.
    rows["rmp_only"] = Professor(name_nexus=None, name_rmp="Rae Only", rmp_id=515151)
    db_session.add(rows["rmp_only"])
    db_session.flush()
    db_session.add(RmpRating(professor_id=rows["rmp_only"].id, overall_quality=3.0,
                             difficulty=3.0, num_ratings=1))

    # Rows with no name at all are outside the cleanup's scope.
    rows["nameless_a"] = _prof(db_session, None)
    rows["nameless_b"] = _prof(db_session, None)

    # The only row of a name survives even though nothing points at it.
    rows["singleton"] = _prof(db_session, "LONELY A")

    # Oldest row is unreferenced and a later duplicate carries old sections:
    # the oldest row is what the sync picks, so it must stay.
    rows["old_orphan"] = _prof(db_session, "ABBEY S D")
    rows["old_orphan_dupes"] = [_prof(db_session, "ABBEY S D") for _ in range(3)]
    rows["later_live"] = _prof(db_session, "ABBEY S D")
    db_session.add(ScheduledSection(professor_id=rows["later_live"].id, course_id=course.id,
                                    quarter_code="20254", enroll_code="22222"))
    db_session.flush()
    # Read ids now: ORM objects of deleted rows can't be refreshed afterwards.
    rows["expected_deleted"] = {p.id for p in rows["dupes"] + rows["old_orphan_dupes"]}
    return rows


def _expected_deleted(rows):
    return rows["expected_deleted"]


def test_deletes_only_unreferenced_duplicates(db_session, seeded):
    before = _ids(db_session)
    deleted = delete_orphans(db_session, batch_size=5000)

    after = _ids(db_session)
    assert deleted == len(_expected_deleted(seeded))
    assert before - after == _expected_deleted(seeded)


@pytest.mark.parametrize("kind", [
    "keeper", "graded", "rated", "scored", "scheduled", "rmp_id", "name_rmp",
    "rmp_only", "nameless_a", "nameless_b", "singleton", "old_orphan", "later_live",
])
def test_keeps_every_kind_of_referenced_or_keeper_row(db_session, seeded, kind):
    delete_orphans(db_session)
    assert db_session.get(Professor, seeded[kind].id) is not None


def test_referencing_rows_untouched(db_session, seeded):
    tables = ["grade_distributions", "rmp_ratings", "gaucho_scores", "scheduled_sections"]
    counts = {t: db_session.execute(text(f"SELECT count(*) FROM {t}")).scalar_one() for t in tables}
    delete_orphans(db_session)
    for t in tables:
        assert db_session.execute(text(f"SELECT count(*) FROM {t}")).scalar_one() == counts[t]


def test_small_batches_delete_the_same_rows(db_session, seeded):
    before = _ids(db_session)
    assert delete_orphans(db_session, batch_size=2) == len(_expected_deleted(seeded))
    assert before - _ids(db_session) == _expected_deleted(seeded)


def test_idempotent(db_session, seeded):
    first = delete_orphans(db_session)
    remaining = _ids(db_session)
    assert first > 0
    assert delete_orphans(db_session) == 0
    assert _ids(db_session) == remaining


def test_dry_run_deletes_nothing(db_session, seeded):
    before = _ids(db_session)
    result = run(db_session, apply=False)
    assert result["deleted"] == 0
    assert result["before"]["deletable"] == len(_expected_deleted(seeded))
    assert _ids(db_session) == before


def test_apply_reports_before_and_after(db_session, seeded):
    result = run(db_session, apply=True, batch_size=3)
    assert result["deleted"] == len(_expected_deleted(seeded))
    assert result["after"]["deletable"] == 0
    assert result["before"]["professors"] - result["after"]["professors"] == result["deleted"]


def test_stats_count_matches_what_is_deleted(db_session, seeded):
    stats = collect_stats(db_session)
    assert stats["deletable"] == delete_orphans(db_session)


def test_row_that_gains_a_reference_after_selection_is_kept(db_session, seeded, course):
    """The delete re-checks references, so a candidate that picks up a
    section between being selected and being deleted survives."""
    target_id = seeded["dupes"][-1].id
    course_id = course.id
    real_execute = db_session.execute
    injected = []

    def execute(statement, params=None, *args, **kwargs):
        result = real_execute(statement, params, *args, **kwargs)
        if not injected and "FOR UPDATE" in str(statement):
            injected.append(True)
            real_execute(text(
                "INSERT INTO scheduled_sections (professor_id, course_id, quarter_code, enroll_code)"
                " VALUES (:p, :c, '20261', '33333')"
            ), {"p": target_id, "c": course_id})
        return result

    db_session.execute = execute
    deleted = delete_orphans(db_session)

    assert injected
    assert deleted == len(_expected_deleted(seeded)) - 1
    assert db_session.get(Professor, target_id) is not None


def test_schema_guard_rejects_unknown_reference(db_session, seeded):
    check_schema(db_session)  # the real schema is fully covered
    db_session.execute(text(
        "CREATE TABLE tmp_prof_ref (professor_id integer REFERENCES professors(id))"
    ))
    with pytest.raises(RuntimeError, match="tmp_prof_ref"):
        check_schema(db_session)


def test_sync_matching_resolves_to_the_same_rows(db_session, seeded):
    """The schedule sync's name matcher picks the same professor id afterwards."""
    names = ["ESCALANTE N", "ESCALANTE N Q", "ESCALANTA N", "ABBEY S D", "ABBEY S",
             "LONELY A", "NOBODY Z"]

    def resolve():
        lookup = _build_professor_lookup(db_session)
        out = {}
        for raw in names:
            match = match_instructor_to_professor(parse_ucsb_instructor(raw), lookup)
            out[raw] = match.professor_id if match else None
        return out

    before = resolve()
    delete_orphans(db_session)
    assert resolve() == before
    assert before["ESCALANTE N"] == seeded["keeper"].id
    assert before["ABBEY S D"] == seeded["old_orphan"].id


def test_sync_does_not_recreate_deleted_rows(db_session, seeded, course):
    delete_orphans(db_session)
    client = MagicMock()
    client.fetch_department_classes.return_value = [{
        "enrollCode": "44444", "courseCancelled": None,
        "instructors": [{"instructor": "ESCALANTE N", "functionCode": "Teaching and in charge"}],
        "timeLocations": [], "enrolledTotal": 1, "maxEnroll": 10,
        "_courseId": "HIST      4A", "_title": "World History", "_quarter": "20261",
    }]
    count = db_session.query(Professor).count()

    stats = sync_department_sections(db_session, "20261", "HIST", client=client,
                                     auto_create_cache={})

    assert stats["auto_created"] == 0
    assert db_session.query(Professor).count() == count
    section = db_session.query(ScheduledSection).filter_by(enroll_code="44444").one()
    assert section.professor_id == seeded["keeper"].id

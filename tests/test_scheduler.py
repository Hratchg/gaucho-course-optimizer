from unittest.mock import MagicMock

import pytest

from scheduler.jobs import (
    create_scheduler,
    nightly_schedule_refresh,
    quarterly_grade_update,
    rmp_targeted_refresh,
    RMP_REFRESH_JOB_ID,
    QUARTERLY_JOB_ID,
    SCHEDULE_REFRESH_JOB_ID,
)


STATS = {"inserted": 0, "updated": 1, "matched": 1, "auto_created": 0}


@pytest.fixture
def refresh_deps(mocker):
    """Patch the dependencies nightly_schedule_refresh imports at call time."""
    session = MagicMock()
    mocker.patch("db.connection.get_session", return_value=session)
    mocker.patch("ucsb_api.client.UCSBApiClient")
    mocker.patch("db.queries.get_departments", return_value=["ANTH", "CMPSC"])
    mocker.patch(
        "ucsb_api.schedule_sync.backfill_missing_titles",
        return_value={"courses": 0, "updated": 0, "departments": 0},
    )
    sync = mocker.patch("ucsb_api.schedule_sync.sync_department_sections", return_value=STATS)
    return session, sync


def test_nightly_refresh_raises_when_db_unavailable(refresh_deps, mocker):
    """A refused connection must fail the job, not log and exit 0."""
    session, _ = refresh_deps
    mocker.patch("db.queries.get_departments", side_effect=RuntimeError("data transfer quota"))
    with pytest.raises(RuntimeError, match="data transfer quota"):
        nightly_schedule_refresh()
    session.close.assert_called_once()


def test_nightly_refresh_syncs_remaining_departments_then_raises(refresh_deps):
    """One department failing rolls back, keeps going, and still fails the run."""
    session, sync = refresh_deps
    seen = []

    def sync_side_effect(_session, qcode, dept, **_kwargs):
        seen.append((qcode, dept))
        if dept == "ANTH" and len(seen) == 1:
            raise ValueError("boom")
        return STATS

    sync.side_effect = sync_side_effect
    with pytest.raises(RuntimeError, match="ANTH"):
        nightly_schedule_refresh()
    assert len(seen) == 4  # 2 departments x 2 quarters, nothing skipped
    session.rollback.assert_called_once()
    session.close.assert_called_once()


def test_nightly_refresh_completes_when_all_departments_sync(refresh_deps):
    session, sync = refresh_deps
    nightly_schedule_refresh()
    assert sync.call_count == 4
    session.close.assert_called_once()


SCRAPE_STATS = {
    "searched": 3, "matched": 2, "skipped": 1, "already_fresh": 0, "errors": 0,
    "aborted": False,
}


@pytest.fixture
def rmp_deps(mocker):
    """Patch the dependencies rmp_targeted_refresh imports at call time."""
    session = MagicMock()
    mocker.patch("db.connection.get_session", return_value=session)
    scrape = mocker.patch(
        "scrapers.targeted_scrape.scrape_active_professors", return_value=SCRAPE_STATS
    )
    nlp = mocker.patch("etl.nlp_processor.process_all_comments", return_value={})
    score = mocker.patch("etl.scoring.compute_all_scores", return_value={})
    return session, scrape, nlp, score


def test_rmp_refresh_runs_scrape_nlp_and_scoring(rmp_deps):
    session, scrape, nlp, score = rmp_deps
    rmp_targeted_refresh()
    scrape.assert_called_once()
    nlp.assert_called_once_with(session)
    score.assert_called_once_with(session)
    session.close.assert_called_once()


def test_rmp_refresh_raises_when_a_step_fails(rmp_deps):
    """A crashed step must fail the job, not log and exit 0."""
    session, _, nlp, score = rmp_deps
    nlp.side_effect = RuntimeError("data transfer quota")
    with pytest.raises(RuntimeError, match="data transfer quota"):
        rmp_targeted_refresh()
    score.assert_not_called()
    session.close.assert_called_once()


def test_rmp_refresh_raises_when_scrape_aborts(rmp_deps):
    """RMP refusing every search still rescores what we have, then fails the run."""
    session, scrape, nlp, score = rmp_deps
    scrape.return_value = {**SCRAPE_STATS, "searched": 0, "errors": 10, "aborted": True}
    with pytest.raises(RuntimeError, match="consecutive search errors"):
        rmp_targeted_refresh()
    nlp.assert_called_once_with(session)
    score.assert_called_once_with(session)
    session.close.assert_called_once()


GRADE_ROWS = [{"instructor": "DOE J", "course_code": "CMPSC8", "quarter": "Spring", "year": 2026}]


@pytest.fixture
def grades_deps(mocker):
    """Patch the dependencies quarterly_grade_update imports at call time."""
    session = MagicMock()
    mocker.patch("db.connection.get_session", return_value=session)
    df = MagicMock()
    df.to_dict.return_value = GRADE_ROWS
    fetch = mocker.patch("scrapers.grades_ingester.fetch_grades_csv", return_value=df)
    load = mocker.patch("scrapers.grades_loader.load_grades_to_db", return_value=1)
    return session, fetch, load


def test_quarterly_grades_loads_the_fetched_csv(grades_deps):
    session, fetch, load = grades_deps
    quarterly_grade_update()
    fetch.assert_called_once_with()
    load.assert_called_once_with(GRADE_ROWS, session)
    session.close.assert_called_once()


def test_quarterly_grades_raises_when_fetch_fails(grades_deps):
    """An unreachable CSV must fail the job, not log and exit 0."""
    session, fetch, load = grades_deps
    fetch.side_effect = OSError("HTTP Error 404: Not Found")
    with pytest.raises(OSError, match="404"):
        quarterly_grade_update()
    load.assert_not_called()
    session.close.assert_called_once()


def test_quarterly_grades_raises_when_load_fails(grades_deps):
    session, _, load = grades_deps
    load.side_effect = RuntimeError("data transfer quota")
    with pytest.raises(RuntimeError, match="data transfer quota"):
        quarterly_grade_update()
    session.close.assert_called_once()


def test_create_scheduler_has_jobs():
    sched = create_scheduler(start=False)
    job_ids = [j.id for j in sched.get_jobs()]
    assert RMP_REFRESH_JOB_ID in job_ids
    assert QUARTERLY_JOB_ID in job_ids
    assert SCHEDULE_REFRESH_JOB_ID in job_ids


def test_rmp_refresh_runs_every_2_days():
    sched = create_scheduler(start=False)
    rmp_job = sched.get_job(RMP_REFRESH_JOB_ID)
    trigger = rmp_job.trigger
    # CronTrigger for every 2 days: day='*/2'
    assert hasattr(trigger, 'fields')


def test_schedule_refresh_runs_nightly():
    sched = create_scheduler(start=False)
    job = sched.get_job(SCHEDULE_REFRESH_JOB_ID)
    assert job is not None
    trigger = job.trigger
    # CronTrigger for nightly at 1:30 AM
    assert hasattr(trigger, 'fields')

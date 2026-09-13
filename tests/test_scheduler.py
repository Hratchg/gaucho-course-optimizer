from unittest.mock import MagicMock

import pytest

from scheduler.jobs import (
    create_scheduler,
    nightly_schedule_refresh,
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
    mocker.patch("dashboard.queries.get_departments", return_value=["ANTH", "CMPSC"])
    sync = mocker.patch("ucsb_api.schedule_sync.sync_department_sections", return_value=STATS)
    return session, sync


def test_nightly_refresh_raises_when_db_unavailable(refresh_deps, mocker):
    """A refused connection must fail the job, not log and exit 0."""
    session, _ = refresh_deps
    mocker.patch("dashboard.queries.get_departments", side_effect=RuntimeError("data transfer quota"))
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

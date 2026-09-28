from unittest.mock import MagicMock

import pytest

from scheduler.jobs import (
    create_scheduler,
    nightly_schedule_refresh,
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

MATCH_STATS = {
    "pass1": {"matched": 1, "ambiguous": 0, "no_candidate": 4, "dept_mismatch": 0},
    "pass2": {"matched": 2, "below_threshold": 7},
    "pass3": {"matched": 0, "still_ambiguous": 1, "no_dept": 0},
    "pass4": {"merged": 0, "skipped_ambiguous": 0, "skipped": True},
    "total_new_matches": 3,
    "total_merges": 0,
}


@pytest.fixture
def rmp_deps(mocker):
    """Patch the dependencies rmp_targeted_refresh imports at call time."""
    session = MagicMock()
    mocker.patch("db.connection.get_session", return_value=session)
    scrape = mocker.patch(
        "scrapers.targeted_scrape.scrape_active_professors", return_value=SCRAPE_STATS
    )
    match = mocker.patch(
        "etl.enhanced_matcher.run_enhanced_matching", return_value=MATCH_STATS
    )
    nlp = mocker.patch("etl.nlp_processor.process_all_comments", return_value={})
    score = mocker.patch("etl.scoring.compute_all_scores", return_value={})
    return session, scrape, match, nlp, score


def test_rmp_refresh_runs_scrape_match_nlp_and_scoring(rmp_deps):
    session, scrape, match, nlp, score = rmp_deps
    rmp_targeted_refresh()
    scrape.assert_called_once()
    match.assert_called_once()
    nlp.assert_called_once_with(session)
    score.assert_called_once_with(session)
    session.close.assert_called_once()


def test_rmp_refresh_matches_between_scrape_and_nlp(rmp_deps, mocker):
    """Newly scraped professors get linked before NLP and scoring see them."""
    _, scrape, match, nlp, score = rmp_deps
    order = mocker.MagicMock()
    order.attach_mock(scrape, "scrape")
    order.attach_mock(match, "match")
    order.attach_mock(nlp, "nlp")
    order.attach_mock(score, "score")
    rmp_targeted_refresh()
    assert [c[0] for c in order.mock_calls] == ["scrape", "match", "nlp", "score"]


def test_rmp_refresh_matches_without_merging_duplicates(rmp_deps):
    """Unattended runs only link; pass 4 (merge + delete) stays manual-only."""
    session, _, match, _, _ = rmp_deps
    rmp_targeted_refresh()
    match.assert_called_once_with(session, min_year=2023, merge_duplicates=False)


def test_rmp_refresh_logs_matching_summary(rmp_deps, caplog):
    """The weekly log is the review trail, so it must say what matching changed."""
    with caplog.at_level("INFO", logger="scheduler.jobs"):
        rmp_targeted_refresh()
    summary = [r.getMessage() for r in caplog.records if r.getMessage().startswith("Matching:")]
    assert len(summary) == 1
    assert "3 new RMP links" in summary[0]
    assert "pass 1: 1" in summary[0]
    assert "pass 2: 2" in summary[0]
    assert "pass 3: 0" in summary[0]


def test_rmp_refresh_raises_and_skips_nlp_when_matching_fails(rmp_deps):
    """A matching crash must fail the job before NLP and scoring run."""
    session, _, match, nlp, score = rmp_deps
    match.side_effect = RuntimeError("matching blew up")
    with pytest.raises(RuntimeError, match="matching blew up"):
        rmp_targeted_refresh()
    nlp.assert_not_called()
    score.assert_not_called()
    session.close.assert_called_once()


def test_rmp_refresh_raises_when_a_step_fails(rmp_deps):
    """A crashed step must fail the job, not log and exit 0."""
    session, _, _, nlp, score = rmp_deps
    nlp.side_effect = RuntimeError("data transfer quota")
    with pytest.raises(RuntimeError, match="data transfer quota"):
        rmp_targeted_refresh()
    score.assert_not_called()
    session.close.assert_called_once()


def test_rmp_refresh_raises_when_scrape_aborts(rmp_deps):
    """RMP refusing every search still rescores what we have, then fails the run."""
    session, scrape, match, nlp, score = rmp_deps
    scrape.return_value = {**SCRAPE_STATS, "searched": 0, "errors": 10, "aborted": True}
    with pytest.raises(RuntimeError, match="consecutive search errors"):
        rmp_targeted_refresh()
    match.assert_called_once()
    nlp.assert_called_once_with(session)
    score.assert_called_once_with(session)
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

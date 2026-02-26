from scheduler.jobs import create_scheduler, NIGHTLY_JOB_ID, QUARTERLY_JOB_ID


def test_create_scheduler_has_jobs():
    sched = create_scheduler(start=False)
    job_ids = [j.id for j in sched.get_jobs()]
    assert NIGHTLY_JOB_ID in job_ids
    assert QUARTERLY_JOB_ID in job_ids

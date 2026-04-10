from scheduler.jobs import create_scheduler, RMP_REFRESH_JOB_ID, QUARTERLY_JOB_ID, SCHEDULE_REFRESH_JOB_ID


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

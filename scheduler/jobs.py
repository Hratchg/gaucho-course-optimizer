import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

NIGHTLY_JOB_ID = "nightly_rmp_refresh"
QUARTERLY_JOB_ID = "quarterly_grade_update"


def nightly_rmp_refresh():
    """Nightly job: scrape RMP → NLP → recompute scores."""
    logger.info("Starting nightly RMP refresh...")
    from scrapers.rmp_scraper import RmpScraper
    from scrapers.rmp_loader import load_rmp_teacher_to_db
    from db.connection import get_session

    session = get_session()
    try:
        scraper = RmpScraper()
        teachers = scraper.fetch_all_teachers()
        for teacher in teachers:
            load_rmp_teacher_to_db(teacher, session)
        logger.info(f"Loaded {len(teachers)} teachers from RMP")
    except Exception as e:
        logger.error(f"Nightly RMP refresh failed: {e}")
    finally:
        session.close()


def quarterly_grade_update():
    """Quarterly job: fetch grades CSV → load → match names → recompute scores."""
    logger.info("Starting quarterly grade update...")
    from scrapers.grades_ingester import fetch_grades_csv
    from scrapers.grades_loader import load_grades_to_db
    from db.connection import get_session

    session = get_session()
    try:
        df = fetch_grades_csv()
        rows = df.to_dict("records")
        inserted = load_grades_to_db(rows, session)
        logger.info(f"Loaded {inserted} new grade records")
    except Exception as e:
        logger.error(f"Quarterly grade update failed: {e}")
    finally:
        session.close()


def create_scheduler(start: bool = True) -> BlockingScheduler:
    """Create and optionally start the APScheduler."""
    scheduler = BlockingScheduler()

    scheduler.add_job(
        nightly_rmp_refresh,
        trigger=CronTrigger(hour=2, minute=0),
        id=NIGHTLY_JOB_ID,
        replace_existing=True,
    )

    scheduler.add_job(
        quarterly_grade_update,
        trigger=CronTrigger(month="1,4,7,10", day=15, hour=3),
        id=QUARTERLY_JOB_ID,
        replace_existing=True,
    )

    if start:
        logger.info("Scheduler started.")
        scheduler.start()

    return scheduler


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_scheduler()

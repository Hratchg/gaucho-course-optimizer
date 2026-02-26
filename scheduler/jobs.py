import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

RMP_REFRESH_JOB_ID = "rmp_targeted_refresh"
QUARTERLY_JOB_ID = "quarterly_grade_update"


def rmp_targeted_refresh():
    """Every-2-days job: targeted RMP scrape -> NLP -> recompute scores."""
    logger.info("Starting targeted RMP refresh...")
    from scrapers.targeted_scrape import scrape_active_professors
    from etl.nlp_processor import process_all_comments
    from etl.scoring import compute_all_scores
    from db.connection import get_session

    session = get_session()
    try:
        scrape_stats = scrape_active_professors(session, min_year=2023)
        logger.info(f"Scrape: {scrape_stats}")

        nlp_stats = process_all_comments(session)
        logger.info(f"NLP: {nlp_stats}")

        score_stats = compute_all_scores(session)
        logger.info(f"Scoring: {score_stats}")
    except Exception as e:
        logger.error(f"RMP refresh failed: {e}")
    finally:
        session.close()


def quarterly_grade_update():
    """Quarterly job: fetch grades CSV -> load -> recompute scores."""
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
        rmp_targeted_refresh,
        trigger=CronTrigger(day="*/2", hour=2, minute=0),
        id=RMP_REFRESH_JOB_ID,
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

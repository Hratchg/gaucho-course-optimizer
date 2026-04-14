import logging
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

load_dotenv()

logger = logging.getLogger(__name__)

RMP_REFRESH_JOB_ID = "rmp_targeted_refresh"
QUARTERLY_JOB_ID = "quarterly_grade_update"
SCHEDULE_REFRESH_JOB_ID = "nightly_schedule_refresh"


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


def nightly_schedule_refresh():
    """Nightly job: fetch next-quarter schedule from UCSB API for all departments."""
    logger.info("Starting nightly schedule refresh...")
    from db.connection import get_session
    from dashboard.queries import get_departments
    from ucsb_api.client import UCSBApiClient, get_next_quarter_code
    from ucsb_api.schedule_sync import sync_department_sections

    session = get_session()
    try:
        client = UCSBApiClient()

        # Determine next quarter code from current date
        import datetime as _dt
        now = _dt.date.today()
        month = now.month
        year = now.year
        if month <= 3:
            current_qcode = f"{year}1"
        elif month <= 6:
            current_qcode = f"{year}2"
        elif month <= 8:
            current_qcode = f"{year}3"
        else:
            current_qcode = f"{year}4"
        next_qcode = get_next_quarter_code(current_qcode)

        departments = get_departments(session)
        total_stats = {"inserted": 0, "updated": 0, "matched": 0, "unmatched": 0}

        # Sync both current and next quarter so students always see data
        for qcode in [current_qcode, next_qcode]:
            logger.info(f"Syncing quarter {qcode}...")
            for dept in departments:
                try:
                    stats = sync_department_sections(
                        session, qcode, dept, client=client
                    )
                    for key in total_stats:
                        total_stats[key] += stats[key]
                except Exception as e:
                    logger.error(f"Failed to sync department {dept} for {qcode}: {e}")

        logger.info(f"Schedule refresh complete: {total_stats}")
    except Exception as e:
        logger.error(f"Schedule refresh failed: {e}")
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

    scheduler.add_job(
        nightly_schedule_refresh,
        trigger=CronTrigger(hour=1, minute=30),
        id=SCHEDULE_REFRESH_JOB_ID,
        replace_existing=True,
    )

    if start:
        logger.info("Scheduler started.")
        scheduler.start()

    return scheduler


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_scheduler()

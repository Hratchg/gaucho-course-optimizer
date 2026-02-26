"""One-shot CLI script to run the full Gaucho pipeline.

Usage:
    python scripts/run_pipeline.py              # full pipeline
    python scripts/run_pipeline.py --scrape     # scrape only
    python scripts/run_pipeline.py --nlp        # NLP only
    python scripts/run_pipeline.py --score      # scoring only
"""
import argparse
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db.connection import get_session

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def run_scrape(session):
    from scrapers.targeted_scrape import scrape_active_professors
    logger.info("=== Phase 1: Targeted RMP Scrape ===")
    stats = scrape_active_professors(session, min_year=2023)
    logger.info(f"Scrape complete: {stats}")
    return stats


def run_nlp(session):
    from etl.nlp_processor import process_all_comments
    logger.info("=== Phase 2: NLP Processing ===")
    stats = process_all_comments(session)
    logger.info(f"NLP complete: {stats}")
    return stats


def run_scoring(session):
    from etl.scoring import compute_all_scores
    logger.info("=== Phase 3: Gaucho Score Computation ===")
    stats = compute_all_scores(session)
    logger.info(f"Scoring complete: {stats}")
    return stats


def main():
    parser = argparse.ArgumentParser(description="Run the Gaucho Course Optimizer pipeline")
    parser.add_argument("--scrape", action="store_true", help="Run RMP scrape only")
    parser.add_argument("--nlp", action="store_true", help="Run NLP processing only")
    parser.add_argument("--score", action="store_true", help="Run scoring only")
    args = parser.parse_args()

    run_all = not (args.scrape or args.nlp or args.score)

    session = get_session()
    try:
        if run_all or args.scrape:
            run_scrape(session)
        if run_all or args.nlp:
            run_nlp(session)
        if run_all or args.score:
            run_scoring(session)

        logger.info("Pipeline finished.")
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted. Partial progress is saved.")
    finally:
        session.close()


if __name__ == "__main__":
    main()

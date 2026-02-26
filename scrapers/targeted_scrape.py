import logging
import time
import random

from db.models import Professor, RmpRating
from scrapers.rmp_loader import get_active_professors, is_stale, load_rmp_teacher_to_db
from scrapers.rmp_scraper import RmpScraper
from etl.name_matcher import normalize_nexus_name, normalize_rmp_name, match_confidence

logger = logging.getLogger(__name__)


def scrape_active_professors(
    session,
    scraper: RmpScraper | None = None,
    min_year: int = 2023,
    max_age_days: int = 2,
    delay: float | None = None,
) -> dict:
    """Scrape RMP for active professors using targeted name search.

    Returns stats dict: {searched, matched, skipped, already_fresh, errors}.
    """
    if scraper is None:
        scraper = RmpScraper()

    professors = get_active_professors(session, min_year=min_year)
    total = len(professors)
    stats = {"searched": 0, "matched": 0, "skipped": 0, "already_fresh": 0, "errors": 0}

    for i, prof in enumerate(professors):
        # Check if data is already fresh
        latest_rating = (
            session.query(RmpRating)
            .filter_by(professor_id=prof.id)
            .order_by(RmpRating.fetched_at.desc())
            .first()
        )
        fetched_at = latest_rating.fetched_at if latest_rating else None
        if not is_stale(fetched_at, max_age_days=max_age_days):
            stats["already_fresh"] += 1
            continue

        # Build search name from Nexus name
        nexus_name = prof.name_nexus
        if not nexus_name:
            stats["skipped"] += 1
            continue

        # Convert "LAST, FIRST" to "First Last" for RMP search
        norm = normalize_nexus_name(nexus_name)
        search_name = norm.title()

        try:
            results = scraper.search_teacher_by_name(search_name)
            stats["searched"] += 1
        except Exception as e:
            logger.error(f"[{i+1}/{total}] Error searching '{search_name}': {e}")
            stats["errors"] += 1
            continue

        # Fuzzy match against results
        best_match = None
        best_confidence = 0
        for teacher in results:
            rmp_name = f"{teacher['first_name']} {teacher['last_name']}"
            norm_rmp = normalize_rmp_name(rmp_name)
            confidence = match_confidence(norm, norm_rmp)
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = teacher

        if best_match and best_confidence >= 70:
            status = "auto" if best_confidence >= 85 else "review"
            try:
                load_rmp_teacher_to_db(
                    best_match, session,
                    nexus_professor_id=prof.id,
                    match_confidence=best_confidence,
                )
                stats["matched"] += 1
                logger.info(
                    f"[{i+1}/{total}] {status.upper()} {nexus_name} -> "
                    f"{best_match['first_name']} {best_match['last_name']} "
                    f"({best_confidence}%)"
                )
            except Exception as e:
                logger.error(f"[{i+1}/{total}] Error saving '{nexus_name}': {e}")
                session.rollback()
                stats["errors"] += 1
        else:
            stats["skipped"] += 1
            logger.debug(
                f"[{i+1}/{total}] SKIP {nexus_name} — "
                f"best match: {best_confidence}%"
            )

        # Rate limiting
        if delay is None:
            time.sleep(random.uniform(2, 4))
        elif delay > 0:
            time.sleep(delay)

    return stats

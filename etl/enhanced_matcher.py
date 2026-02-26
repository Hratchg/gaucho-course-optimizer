"""Enhanced multi-pass professor matching engine.

All passes are local (no API calls) — they match existing Nexus professors
against existing RMP professors already in the database.
"""

import logging
from collections import defaultdict

from sqlalchemy.orm import Session

from db.models import Professor, GradeDistribution
from etl.name_utils import parse_nexus_name, is_initial_only, initial_matches, find_duplicate_pairs
from etl.department_mapper import departments_match
from etl.name_matcher import normalize_nexus_name, normalize_rmp_name, match_confidence

logger = logging.getLogger(__name__)


def _get_unmatched_nexus(session: Session, min_year: int = 2023) -> list[Professor]:
    """Get Nexus professors with no RMP link who taught since min_year."""
    return (
        session.query(Professor)
        .join(GradeDistribution, GradeDistribution.professor_id == Professor.id)
        .filter(
            Professor.name_nexus.isnot(None),
            Professor.rmp_id.is_(None),
            GradeDistribution.year >= min_year,
        )
        .group_by(Professor.id)
        .all()
    )


def _get_unlinked_rmp(session: Session) -> list[Professor]:
    """Get RMP-only professors (have rmp_id but no Nexus name)."""
    return (
        session.query(Professor)
        .filter(
            Professor.rmp_id.isnot(None),
            Professor.name_nexus.is_(None),
        )
        .all()
    )


def _link_professor(
    session: Session,
    nexus_prof: Professor,
    rmp_prof: Professor,
    confidence: float,
    dry_run: bool = False,
) -> bool:
    """Link a Nexus professor to an RMP professor.

    Copies rmp_id, name_rmp, and match_confidence from rmp_prof to nexus_prof.
    Returns True if linked, False if collision detected.
    """
    # Collision guard: check rmp_id uniqueness
    existing = (
        session.query(Professor)
        .filter(Professor.rmp_id == rmp_prof.rmp_id, Professor.id != nexus_prof.id)
        .first()
    )
    if existing and existing.name_nexus is not None:
        logger.warning(
            f"Collision: RMP ID {rmp_prof.rmp_id} already linked to "
            f"{existing.name_nexus} (id={existing.id}), skipping {nexus_prof.name_nexus}"
        )
        return False

    if dry_run:
        return True

    # Save values before clearing to avoid unique constraint violation
    saved_rmp_id = rmp_prof.rmp_id
    saved_name_rmp = rmp_prof.name_rmp

    # Transfer ratings from the RMP-only professor to the Nexus professor
    for rating in list(rmp_prof.rmp_ratings):
        rating.professor_id = nexus_prof.id

    # Clear rmp_id on the RMP-only row and flush the rating transfers
    rmp_prof.rmp_id = None
    session.flush()

    # Expire so SQLAlchemy doesn't try to cascade-nullify already-transferred ratings
    session.expire(rmp_prof)

    # Remove the now-orphaned RMP-only row
    session.delete(rmp_prof)
    session.flush()

    # Now safe to set the rmp_id on the Nexus professor
    nexus_prof.rmp_id = saved_rmp_id
    nexus_prof.name_rmp = saved_name_rmp
    nexus_prof.match_confidence = confidence
    session.flush()
    return True


def _pass1_initial_match(
    session: Session,
    unmatched: list[Professor],
    rmp_profs: list[Professor],
    dry_run: bool = False,
) -> dict:
    """Pass 1: Match initial-only Nexus names to RMP professors by last name + initial.

    Links only when exactly 1 candidate exists. Confidence 90 (dept match) or 75 (no dept).
    """
    stats = {"matched": 0, "ambiguous": 0, "no_candidate": 0}

    # Index RMP professors by lowercase last name
    rmp_by_last: dict[str, list[Professor]] = defaultdict(list)
    for rmp in rmp_profs:
        if rmp.name_rmp:
            parts = rmp.name_rmp.strip().split()
            if parts:
                last = parts[-1].lower()
                rmp_by_last[last].append(rmp)

    for prof in unmatched:
        if not is_initial_only(prof.name_nexus):
            continue

        parsed = parse_nexus_name(prof.name_nexus)
        last = parsed["last"]
        initial = parsed["first"]

        candidates = [
            rmp for rmp in rmp_by_last.get(last, [])
            if rmp.name_rmp and initial_matches(initial, rmp.name_rmp.split()[0])
        ]

        if len(candidates) == 0:
            stats["no_candidate"] += 1
        elif len(candidates) == 1:
            rmp_prof = candidates[0]
            dept_match = departments_match(prof.department, rmp_prof.department)
            confidence = 90.0 if dept_match else 75.0

            if _link_professor(session, prof, rmp_prof, confidence, dry_run):
                stats["matched"] += 1
                logger.info(
                    f"Pass 1: {prof.name_nexus} -> {rmp_prof.name_rmp} "
                    f"(conf={confidence}, dept={'Y' if dept_match else 'N'})"
                )
        else:
            stats["ambiguous"] += 1
            logger.debug(
                f"Pass 1: {prof.name_nexus} ambiguous — {len(candidates)} candidates"
            )

    if not dry_run:
        session.commit()

    return stats


def _pass2_fullname_fuzzy(
    session: Session,
    min_year: int = 2023,
    dry_run: bool = False,
) -> dict:
    """Pass 2: Fuzzy match full-name Nexus professors against unlinked RMP records.

    Threshold 85+. Department match boosts confidence by 5.
    """
    stats = {"matched": 0, "below_threshold": 0}

    # Re-query after Pass 1 may have changed state
    unmatched = _get_unmatched_nexus(session, min_year)
    rmp_profs = _get_unlinked_rmp(session)

    if not rmp_profs:
        return stats

    for prof in unmatched:
        if is_initial_only(prof.name_nexus):
            continue

        norm_nexus = normalize_nexus_name(prof.name_nexus)
        best_score = 0
        best_rmp = None

        for rmp in rmp_profs:
            if not rmp.name_rmp:
                continue
            norm_rmp = normalize_rmp_name(rmp.name_rmp)
            score = match_confidence(norm_nexus, norm_rmp)
            if score > best_score:
                best_score = score
                best_rmp = rmp

        if best_score >= 85 and best_rmp:
            dept_match = departments_match(prof.department, best_rmp.department)
            confidence = min(best_score + (5 if dept_match else 0), 100.0)

            if _link_professor(session, prof, best_rmp, confidence, dry_run):
                stats["matched"] += 1
                # Remove from candidate pool
                rmp_profs.remove(best_rmp)
                logger.info(
                    f"Pass 2: {prof.name_nexus} -> {best_rmp.name_rmp} "
                    f"(conf={confidence})"
                )
        else:
            stats["below_threshold"] += 1

    if not dry_run:
        session.commit()

    return stats


def _pass3_dept_disambiguation(
    session: Session,
    min_year: int = 2023,
    dry_run: bool = False,
) -> dict:
    """Pass 3: For ambiguous initial-only names, use department to narrow to 1 candidate."""
    stats = {"matched": 0, "still_ambiguous": 0, "no_dept": 0}

    unmatched = _get_unmatched_nexus(session, min_year)
    rmp_profs = _get_unlinked_rmp(session)

    # Index RMP by last name
    rmp_by_last: dict[str, list[Professor]] = defaultdict(list)
    for rmp in rmp_profs:
        if rmp.name_rmp:
            parts = rmp.name_rmp.strip().split()
            if parts:
                last = parts[-1].lower()
                rmp_by_last[last].append(rmp)

    for prof in unmatched:
        if not is_initial_only(prof.name_nexus):
            continue
        if not prof.department:
            stats["no_dept"] += 1
            continue

        parsed = parse_nexus_name(prof.name_nexus)
        last = parsed["last"]
        initial = parsed["first"]

        # Find all candidates matching last name + initial
        candidates = [
            rmp for rmp in rmp_by_last.get(last, [])
            if rmp.name_rmp and initial_matches(initial, rmp.name_rmp.split()[0])
        ]

        if len(candidates) <= 1:
            continue  # Already handled by Pass 1

        # Filter by department
        dept_matches = [
            rmp for rmp in candidates
            if departments_match(prof.department, rmp.department)
        ]

        if len(dept_matches) == 1:
            rmp_prof = dept_matches[0]
            if _link_professor(session, prof, rmp_prof, 90.0, dry_run):
                stats["matched"] += 1
                logger.info(
                    f"Pass 3: {prof.name_nexus} ({prof.department}) -> "
                    f"{rmp_prof.name_rmp} (dept disambiguated)"
                )
        else:
            stats["still_ambiguous"] += 1

    if not dry_run:
        session.commit()

    return stats


def _pass4_deduplication(
    session: Session,
    min_year: int = 2023,
    dry_run: bool = False,
) -> dict:
    """Pass 4: Merge duplicate Nexus professor pairs (abbreviated + full name).

    Transfers grade records from the abbreviated-name professor to the full-name one.
    """
    stats = {"merged": 0}

    # Get all Nexus professors (not just unmatched — we want to find duplicates)
    all_nexus = (
        session.query(Professor)
        .filter(Professor.name_nexus.isnot(None))
        .all()
    )

    names_with_dept = [
        {"id": p.id, "name": p.name_nexus, "department": p.department or ""}
        for p in all_nexus
    ]

    pairs = find_duplicate_pairs(names_with_dept)

    for abbr_info, full_info in pairs:
        abbr = session.get(Professor, abbr_info["id"])
        full = session.get(Professor, full_info["id"])

        if not abbr or not full:
            continue

        # If the abbreviated one has an RMP link but the full one doesn't, transfer it
        if abbr.rmp_id and not full.rmp_id:
            saved_rmp_id = abbr.rmp_id
            full.name_rmp = abbr.name_rmp
            full.match_confidence = abbr.match_confidence
            for rating in list(abbr.rmp_ratings):
                rating.professor_id = full.id
            abbr.rmp_id = None
            session.flush()
            full.rmp_id = saved_rmp_id

        # Transfer grade records from abbreviated to full
        if not dry_run:
            for grade in list(abbr.grades):
                # Check for duplicate (same course + quarter + year)
                existing = (
                    session.query(GradeDistribution)
                    .filter_by(
                        professor_id=full.id,
                        course_id=grade.course_id,
                        quarter=grade.quarter,
                        year=grade.year,
                    )
                    .first()
                )
                if existing:
                    # Duplicate — delete the abbreviated prof's copy
                    session.delete(grade)
                else:
                    grade.professor_id = full.id

            # Transfer any scores
            for score in list(abbr.scores):
                score.professor_id = full.id

            session.flush()
            session.expire(abbr)
            session.delete(abbr)
            session.flush()

        stats["merged"] += 1
        logger.info(
            f"Pass 4: Merged {abbr_info['name']} -> {full_info['name']} "
            f"(dept={full_info['department']})"
        )

    if not dry_run:
        session.commit()

    return stats


def run_enhanced_matching(
    session: Session,
    min_year: int = 2023,
    dry_run: bool = False,
) -> dict:
    """Orchestrate all four matching passes.

    Args:
        session: SQLAlchemy session
        min_year: Only consider professors active since this year
        dry_run: If True, don't modify the database

    Returns:
        Combined stats dict with per-pass results
    """
    logger.info("=== Enhanced Professor Matching ===")

    # Get initial state
    unmatched = _get_unmatched_nexus(session, min_year)
    rmp_profs = _get_unlinked_rmp(session)

    logger.info(f"Starting: {len(unmatched)} unmatched Nexus, {len(rmp_profs)} unlinked RMP")

    # Pass 1
    logger.info("--- Pass 1: Initial Match ---")
    p1 = _pass1_initial_match(session, unmatched, rmp_profs, dry_run)
    logger.info(f"Pass 1 results: {p1}")

    # Pass 2
    logger.info("--- Pass 2: Full-Name Fuzzy ---")
    p2 = _pass2_fullname_fuzzy(session, min_year, dry_run)
    logger.info(f"Pass 2 results: {p2}")

    # Pass 3
    logger.info("--- Pass 3: Department Disambiguation ---")
    p3 = _pass3_dept_disambiguation(session, min_year, dry_run)
    logger.info(f"Pass 3 results: {p3}")

    # Pass 4
    logger.info("--- Pass 4: Nexus Deduplication ---")
    p4 = _pass4_deduplication(session, min_year, dry_run)
    logger.info(f"Pass 4 results: {p4}")

    total_new = p1["matched"] + p2["matched"] + p3["matched"]
    total_merged = p4["merged"]
    logger.info(
        f"=== Done: {total_new} new matches, {total_merged} merges ==="
    )

    return {
        "pass1": p1,
        "pass2": p2,
        "pass3": p3,
        "pass4": p4,
        "total_new_matches": total_new,
        "total_merges": total_merged,
    }

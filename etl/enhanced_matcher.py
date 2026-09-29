"""Enhanced multi-pass professor matching engine.

All passes are local (no API calls) — they match existing Nexus professors
against existing RMP professors already in the database.
"""

import logging
from collections import defaultdict

from sqlalchemy import delete, update
from sqlalchemy.orm import Session

from db.models import (
    Professor,
    GradeDistribution,
    GauchoScore,
    RmpRating,
    ScheduledSection,
)
from etl.name_utils import (
    parse_nexus_name,
    is_initial_only,
    initial_matches,
    find_duplicate_pairs,
    truncated_name_match,
)
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
    consumed_rmp_ids: set[int] | None = None,
) -> dict:
    """Pass 1: Match initial-only Nexus names to RMP professors by last name + initial.

    Links only when exactly 1 candidate exists AND departments match.
    Confidence is always 90. Cross-department initial-only links (formerly
    confidence 75) are skipped — surname+initial alone is too weak to publish
    as fact when the departments disagree (DATA-1 / BUG-9).
    """
    stats = {"matched": 0, "ambiguous": 0, "no_candidate": 0, "dept_mismatch": 0}
    consumed = consumed_rmp_ids if consumed_rmp_ids is not None else set()

    # Index RMP professors by every surname token (not the given name) so
    # multi-word names like "Van Der Berg" are findable as van, der, or berg.
    rmp_by_last: dict[str, list[Professor]] = defaultdict(list)
    for rmp in rmp_profs:
        if rmp.id in consumed:
            continue
        if rmp.name_rmp:
            parts = [p.lower().strip(".,") for p in rmp.name_rmp.replace("-", " ").split() if p.strip()]
            surname_tokens = parts[1:] if len(parts) > 1 else parts
            for part in surname_tokens:
                rmp_by_last[part].append(rmp)

    for prof in unmatched:
        if not is_initial_only(prof.name_nexus):
            continue

        parsed = parse_nexus_name(prof.name_nexus)
        last = parsed["last"]
        initial = parsed["first"]

        candidates = [
            rmp for rmp in rmp_by_last.get(last, [])
            if rmp.id not in consumed
            and rmp.name_rmp
            and initial_matches(initial, rmp.name_rmp.split()[0])
        ]

        if len(candidates) == 0:
            stats["no_candidate"] += 1
        elif len(candidates) == 1:
            rmp_prof = candidates[0]
            if not departments_match(prof.department, rmp_prof.department):
                stats["dept_mismatch"] += 1
                logger.debug(
                    f"Pass 1: {prof.name_nexus} -> {rmp_prof.name_rmp} "
                    f"skipped — department mismatch "
                    f"({prof.department!r} vs {rmp_prof.department!r})"
                )
                continue

            if _link_professor(session, prof, rmp_prof, 90.0, dry_run):
                consumed.add(rmp_prof.id)
                rmp_by_last[last] = [r for r in rmp_by_last[last] if r.id != rmp_prof.id]
                stats["matched"] += 1
                logger.info(
                    f"Pass 1: {prof.name_nexus} [id={prof.id}] -> {rmp_prof.name_rmp} "
                    f"(conf=90, dept=Y)"
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
    consumed_rmp_ids: set[int] | None = None,
) -> dict:
    """Pass 2: Fuzzy match full-name Nexus professors against unlinked RMP records.

    Threshold 85+. Department match boosts confidence by 5.
    """
    stats = {"matched": 0, "below_threshold": 0}
    consumed = consumed_rmp_ids if consumed_rmp_ids is not None else set()

    # Re-query after Pass 1 may have changed state
    unmatched = _get_unmatched_nexus(session, min_year)
    rmp_profs = [r for r in _get_unlinked_rmp(session) if r.id not in consumed]

    if not rmp_profs:
        return stats

    for prof in unmatched:
        if is_initial_only(prof.name_nexus):
            continue

        norm_nexus = normalize_nexus_name(prof.name_nexus)
        best_score = 0
        best_rmp = None

        for rmp in rmp_profs:
            if rmp.id in consumed or not rmp.name_rmp:
                continue
            norm_rmp = normalize_rmp_name(rmp.name_rmp)
            score = match_confidence(norm_nexus, norm_rmp)
            if score < 85 and truncated_name_match(prof.name_nexus or "", rmp.name_rmp):
                score = 90
            if score > best_score:
                best_score = score
                best_rmp = rmp

        if best_score >= 85 and best_rmp:
            dept_match = departments_match(prof.department, best_rmp.department)
            confidence = min(best_score + (5 if dept_match else 0), 100.0)

            if _link_professor(session, prof, best_rmp, confidence, dry_run):
                consumed.add(best_rmp.id)
                stats["matched"] += 1
                # Remove from candidate pool
                rmp_profs.remove(best_rmp)
                logger.info(
                    f"Pass 2: {prof.name_nexus} [id={prof.id}] -> {best_rmp.name_rmp} "
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
    consumed_rmp_ids: set[int] | None = None,
) -> dict:
    """Pass 3: For ambiguous initial-only names, use department to narrow to 1 candidate."""
    stats = {"matched": 0, "still_ambiguous": 0, "no_dept": 0}
    consumed = consumed_rmp_ids if consumed_rmp_ids is not None else set()

    unmatched = _get_unmatched_nexus(session, min_year)
    rmp_profs = [r for r in _get_unlinked_rmp(session) if r.id not in consumed]

    # Index RMP by every surname token (not the given name).
    rmp_by_last: dict[str, list[Professor]] = defaultdict(list)
    for rmp in rmp_profs:
        if rmp.name_rmp:
            parts = [p.lower().strip(".,") for p in rmp.name_rmp.replace("-", " ").split() if p.strip()]
            surname_tokens = parts[1:] if len(parts) > 1 else parts
            for part in surname_tokens:
                rmp_by_last[part].append(rmp)

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
            if rmp.id not in consumed
            and rmp.name_rmp
            and initial_matches(initial, rmp.name_rmp.split()[0])
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
                consumed.add(rmp_prof.id)
                rmp_by_last[last] = [r for r in rmp_by_last[last] if r.id != rmp_prof.id]
                stats["matched"] += 1
                logger.info(
                    f"Pass 3: {prof.name_nexus} [id={prof.id}] ({prof.department}) -> "
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

    The abbreviated-name row ("HUANG L") is the loser and is deleted; the
    full-name row ("HUANG LEI") survives. Before the delete, every row that
    references the loser is moved (see _merge_pair). Each merge runs in its
    own SAVEPOINT, so a failure rolls back that pair only and is counted in
    ``failed``; merges that succeeded are still committed.

    A pair is skipped, untouched, when:
      - the abbreviated name matches more than one full name in the same
        department (``skipped_ambiguous``, BUG-10);
      - both rows have their own RMP identity (``skipped_rmp_conflict``):
        two RMP profiles means two people or an RMP duplicate, and either
        way one profile's ratings would have to be thrown away;
      - both rows have a grade row for the same (course, quarter, year) with
        different numbers (``skipped_grade_conflict``). See _merge_blocker
        for the grade rule.

    With ``dry_run=True`` nothing is written, flushed or changed in the
    session; ``merged`` counts the pairs that would merge.

    Gaucho Scores are derived data. The survivor keeps its own score rows,
    and the loser's score for a course the survivor already has is dropped,
    so the survivor's scores reflect pre-merge grades until the next
    ``etl.scoring.compute_all_scores`` run (weekly refresh, or
    ``scripts/run_pipeline.py --score``) recomputes them.
    """
    stats = {
        "merged": 0,
        "skipped_ambiguous": 0,
        "skipped_rmp_conflict": 0,
        "skipped_grade_conflict": 0,
        "failed": 0,
        "grades_moved": 0,
        "grades_deduplicated": 0,
        "sections_moved": 0,
        "ratings_moved": 0,
        "scores_moved": 0,
        "scores_dropped": 0,
    }

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

    # An abbreviated name that pairs with more than one full name in the same
    # department is ambiguous — merging would attribute grades by iteration
    # order (BUG-10). Group first; only mutate 1:1 pairs.
    pairs_by_abbr: dict[int, list[tuple[dict, dict]]] = defaultdict(list)
    for abbr_info, full_info in pairs:
        pairs_by_abbr[abbr_info["id"]].append((abbr_info, full_info))

    # Sorted so runs are reproducible and the audit log reads in id order.
    for abbr_id, group in sorted(pairs_by_abbr.items()):
        if len(group) != 1:
            stats["skipped_ambiguous"] += 1
            names = ", ".join(sorted({full["name"] for _abbr, full in group}))
            logger.warning(
                f"Pass 4: skipped ambiguous merge for professor id={abbr_id} "
                f"— matches {len(group)} full names ({names})"
            )
            continue

        abbr_info, full_info = group[0]
        abbr = session.get(Professor, abbr_info["id"])
        full = session.get(Professor, full_info["id"])

        if not abbr or not full:
            continue

        pair = (
            f"professor id={abbr.id} ({abbr.name_nexus!r}) into "
            f"id={full.id} ({full.name_nexus!r}), dept={full.department!r}"
        )

        blocker, duplicate_grade_ids = _merge_blocker(session, abbr, full)
        if blocker is not None:
            stats[f"skipped_{blocker}"] += 1
            logger.warning(f"Pass 4: skipped merging {pair} — {blocker.replace('_', ' ')}")
            continue

        if dry_run:
            stats["merged"] += 1
            logger.info(f"Pass 4 (dry run): would merge {pair}")
            continue

        try:
            with session.begin_nested():
                moved = _merge_pair(session, abbr, full, duplicate_grade_ids)
        except Exception:
            stats["failed"] += 1
            logger.exception(f"Pass 4: merge failed and was rolled back for {pair}")
            continue

        stats["merged"] += 1
        for key, count in moved.items():
            stats[key] += count
        logger.info(
            f"Pass 4: merged {pair}: "
            + ", ".join(f"{key}={count}" for key, count in moved.items())
        )

    if not dry_run:
        session.commit()

    return stats


# The per-student counts on a grade row, used to tell a duplicate from a conflict.
_GRADE_VALUE_FIELDS = (
    "a_plus", "a", "a_minus", "b_plus", "b", "b_minus",
    "c_plus", "c", "c_minus", "d_plus", "d", "d_minus", "f", "avg_gpa",
)


def _has_rmp_identity(session: Session, prof: Professor) -> bool:
    if prof.rmp_id is not None:
        return True
    return (
        session.query(RmpRating.id).filter(RmpRating.professor_id == prof.id).first()
        is not None
    )


def _merge_blocker(
    session: Session, loser: Professor, survivor: Professor
) -> tuple[str | None, list[int]]:
    """Decide whether a pair can merge. Read-only.

    Returns ``(reason, duplicate_grade_ids)``. ``reason`` is None when the
    merge is safe, otherwise ``"rmp_conflict"`` or ``"grade_conflict"``.

    Grade rule for a (course, quarter, year) both rows have:
      - identical counts and avg_gpa: it is one Daily Nexus record loaded
        twice under two spellings of the name. The loser's copy is listed in
        ``duplicate_grade_ids`` and dropped; the survivor's row is kept.
      - any difference: two instructors taught that course that quarter, or
        the data disagrees. Summing would double count a re-loaded record and
        keeping either row would lose students, so the pair is not merged.
    """
    if _has_rmp_identity(session, loser) and _has_rmp_identity(session, survivor):
        return "rmp_conflict", []

    def rows(prof_id: int) -> list[GradeDistribution]:
        return (
            session.query(GradeDistribution)
            .filter(GradeDistribution.professor_id == prof_id)
            .order_by(GradeDistribution.id)
            .all()
        )

    survivor_by_key: dict[tuple, list[GradeDistribution]] = defaultdict(list)
    for grade in rows(survivor.id):
        survivor_by_key[(grade.course_id, grade.quarter, grade.year)].append(grade)

    duplicates = []
    for grade in rows(loser.id):
        matches = survivor_by_key.get((grade.course_id, grade.quarter, grade.year))
        if not matches:
            continue
        values = tuple(getattr(grade, f) for f in _GRADE_VALUE_FIELDS)
        if not any(
            values == tuple(getattr(m, f) for f in _GRADE_VALUE_FIELDS) for m in matches
        ):
            return "grade_conflict", []
        duplicates.append(grade.id)

    return None, duplicates


def _move_grades(
    session: Session, loser_id: int, survivor_id: int, duplicate_ids: list[int]
) -> tuple[int, int]:
    dropped = 0
    if duplicate_ids:
        dropped = session.execute(
            delete(GradeDistribution).where(GradeDistribution.id.in_(duplicate_ids))
        ).rowcount
    moved = session.execute(
        update(GradeDistribution)
        .where(GradeDistribution.professor_id == loser_id)
        .values(professor_id=survivor_id)
    ).rowcount
    return moved, dropped


def _move_scores(session: Session, loser_id: int, survivor_id: int) -> tuple[int, int]:
    """Move the loser's scores; drop the ones uq_gaucho_score_pair would reject."""
    survivor_courses = [
        course_id
        for (course_id,) in session.query(GauchoScore.course_id).filter(
            GauchoScore.professor_id == survivor_id
        )
    ]
    dropped = 0
    if survivor_courses:
        dropped = session.execute(
            delete(GauchoScore).where(
                GauchoScore.professor_id == loser_id,
                GauchoScore.course_id.in_(survivor_courses),
            )
        ).rowcount
    moved = session.execute(
        update(GauchoScore)
        .where(GauchoScore.professor_id == loser_id)
        .values(professor_id=survivor_id)
    ).rowcount
    return moved, dropped


def _move_sections(session: Session, loser_id: int, survivor_id: int) -> int:
    return session.execute(
        update(ScheduledSection)
        .where(ScheduledSection.professor_id == loser_id)
        .values(professor_id=survivor_id)
    ).rowcount


def _move_rmp_link(session: Session, loser: Professor, survivor: Professor) -> int:
    """Move the loser's RMP link and ratings (comments follow their rating).

    _merge_blocker has already ensured the survivor has no RMP identity.
    """
    ratings_moved = session.execute(
        update(RmpRating)
        .where(RmpRating.professor_id == loser.id)
        .values(professor_id=survivor.id)
    ).rowcount
    if loser.rmp_id is not None:
        rmp_id, name_rmp, confidence = loser.rmp_id, loser.name_rmp, loser.match_confidence
        loser.rmp_id = None
        session.flush()  # free the unique rmp_id before the survivor takes it
        survivor.rmp_id = rmp_id
        survivor.name_rmp = name_rmp
        survivor.match_confidence = confidence
    return ratings_moved


def _merge_pair(
    session: Session,
    loser: Professor,
    survivor: Professor,
    duplicate_grade_ids: list[int],
) -> dict:
    """Move everything referencing ``loser`` onto ``survivor``, then delete it.

    Covers every table with a professors.id foreign key: grade_distributions,
    gaucho_scores, scheduled_sections and rmp_ratings (rmp_comments hang off
    rmp_ratings). The caller runs this inside a SAVEPOINT; if anything else
    still references the loser, the delete raises and the SAVEPOINT rolls
    the whole pair back.
    """
    ratings_moved = _move_rmp_link(session, loser, survivor)
    grades_moved, grades_dropped = _move_grades(
        session, loser.id, survivor.id, duplicate_grade_ids
    )
    scores_moved, scores_dropped = _move_scores(session, loser.id, survivor.id)
    sections_moved = _move_sections(session, loser.id, survivor.id)

    session.flush()
    # Reload the loser's (now empty) collections so the ORM delete below has
    # nothing to null out — a leftover row would fail loudly instead.
    session.expire(loser)
    session.expire(survivor)
    session.delete(loser)
    session.flush()

    return {
        "grades_moved": grades_moved,
        "grades_deduplicated": grades_dropped,
        "sections_moved": sections_moved,
        "ratings_moved": ratings_moved,
        "scores_moved": scores_moved,
        "scores_dropped": scores_dropped,
    }


def run_enhanced_matching(
    session: Session,
    min_year: int = 2023,
    dry_run: bool = False,
    merge_duplicates: bool = True,
) -> dict:
    """Orchestrate all four matching passes.

    Args:
        session: SQLAlchemy session
        min_year: Only consider professors active since this year
        dry_run: If True, don't modify the database
        merge_duplicates: Run pass 4, which deletes abbreviated-name professor
            rows after moving their grades onto a full-name row. Unattended
            runs pass False: a wrong merge can't be undone without a backup.

    Returns:
        Combined stats dict with per-pass results
    """
    logger.info("=== Enhanced Professor Matching ===")

    # Get initial state
    unmatched = _get_unmatched_nexus(session, min_year)
    rmp_profs = _get_unlinked_rmp(session)
    consumed_rmp_ids: set[int] = set()

    logger.info(f"Starting: {len(unmatched)} unmatched Nexus, {len(rmp_profs)} unlinked RMP")

    # Pass 1
    logger.info("--- Pass 1: Initial Match ---")
    p1 = _pass1_initial_match(session, unmatched, rmp_profs, dry_run, consumed_rmp_ids)
    logger.info(f"Pass 1 results: {p1}")

    # Pass 2
    logger.info("--- Pass 2: Full-Name Fuzzy ---")
    p2 = _pass2_fullname_fuzzy(session, min_year, dry_run, consumed_rmp_ids)
    logger.info(f"Pass 2 results: {p2}")

    # Pass 3
    logger.info("--- Pass 3: Department Disambiguation ---")
    p3 = _pass3_dept_disambiguation(session, min_year, dry_run, consumed_rmp_ids)
    logger.info(f"Pass 3 results: {p3}")

    # Pass 4
    if merge_duplicates:
        logger.info("--- Pass 4: Nexus Deduplication ---")
        p4 = _pass4_deduplication(session, min_year, dry_run)
        logger.info(f"Pass 4 results: {p4}")
    else:
        p4 = {"merged": 0, "skipped_ambiguous": 0, "skipped": True}
        logger.info("--- Pass 4: Nexus Deduplication skipped (merge_duplicates=False) ---")

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

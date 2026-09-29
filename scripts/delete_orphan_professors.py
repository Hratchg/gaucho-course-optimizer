"""Delete the duplicate professor rows left behind by the old nightly-sync bug.

Before PR #1 (commit 4337c14) the schedule sync auto-created a new
``professors`` row for every UCSB instructor it failed to match, every night,
so names like "ESCALANTE N" ended up with dozens of identical rows that nothing
points at. This script removes those rows.

A row is deleted only when all of the following hold:

* nothing references it: no ``grade_distributions``, ``rmp_ratings``,
  ``gaucho_scores`` or ``scheduled_sections`` row has its id;
* it has no RMP identity (``rmp_id`` and ``name_rmp`` are both NULL);
* it is not the keeper for its name, meaning an older row (lower id) with the
  same ``name_nexus`` exists. The oldest row of every name always survives,
  and rows with no ``name_nexus`` are never touched.

The keeper rule matters because the schedule sync
(``ucsb_api.schedule_sync._build_professor_lookup``) and the grades loader
(``scrapers.grades_loader``) both walk professors oldest-first and take the
first row whose name matches. Keeping the oldest row of every distinct
``name_nexus`` means both still resolve every name to the same id after the
cleanup, so tomorrow's sync neither recreates the rows nor attaches a section
to someone else.

Dry-run is the default and only reads. ``--apply`` deletes in batches, one
transaction per batch: it locks a batch of candidates, re-checks every
condition in a fresh statement, and deletes only the rows that still qualify.
Rows that gained a reference in the meantime are left alone, and the foreign
keys (ON DELETE NO ACTION) remain a final backstop. Re-running is safe; a
second run finds nothing to delete.

Usage:
    python scripts/delete_orphan_professors.py            # dry run
    python scripts/delete_orphan_professors.py --apply    # delete
"""

import argparse
import logging
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

logger = logging.getLogger("delete_orphan_professors")

# Every (table, column) that holds a professors.id. The script refuses to run
# if the database has a foreign key to professors that is not listed here.
REFERENCING_COLUMNS: tuple[tuple[str, str], ...] = (
    ("grade_distributions", "professor_id"),
    ("rmp_ratings", "professor_id"),
    ("gaucho_scores", "professor_id"),
    ("scheduled_sections", "professor_id"),
)

DEFAULT_BATCH_SIZE = 5000


def _orphan_predicate(alias: str) -> str:
    """SQL that is true for a deletable row of ``professors`` aliased as ``alias``."""
    unreferenced = "\n".join(
        f"  AND NOT EXISTS (SELECT 1 FROM {table} r WHERE r.{column} = {alias}.id)"
        for table, column in REFERENCING_COLUMNS
    )
    return (
        f"{alias}.rmp_id IS NULL\n"
        f"  AND {alias}.name_rmp IS NULL\n"
        f"{unreferenced}\n"
        # Keeper rule: an older row with the same name must exist. Rows with a
        # NULL name_nexus never satisfy this and are left alone. (Keep this a
        # plain EXISTS: OR-ing it with anything stops Postgres turning it into
        # a hash semi-join and the query takes minutes instead of a second.)
        f"  AND EXISTS (\n"
        f"    SELECT 1 FROM professors k\n"
        f"    WHERE k.name_nexus = {alias}.name_nexus AND k.id < {alias}.id)"
    )


def check_schema(session: Session) -> None:
    """Abort if some foreign key to professors is not covered by the re-check."""
    rows = session.execute(text("""
        SELECT c.conrelid::regclass::text AS tbl, a.attname AS col
        FROM pg_constraint c
        JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY (c.conkey)
        WHERE c.contype = 'f' AND c.confrelid = 'professors'::regclass
    """)).all()
    found = {(tbl.split(".")[-1], col) for tbl, col in rows}
    unknown = found - set(REFERENCING_COLUMNS)
    if unknown:
        raise RuntimeError(
            "professors is referenced by columns this script does not check: "
            f"{sorted(unknown)}. Add them to REFERENCING_COLUMNS before running."
        )


def collect_stats(session: Session, sample_size: int = 10) -> dict:
    """Count what a run would delete, without changing anything."""
    pred = _orphan_predicate("p")
    stats = {
        "professors": session.execute(text("SELECT count(*) FROM professors")).scalar_one(),
        "distinct_name_nexus": session.execute(
            text("SELECT count(DISTINCT name_nexus) FROM professors")
        ).scalar_one(),
        "deletable": session.execute(
            text(f"SELECT count(*) FROM professors p WHERE {pred}")
        ).scalar_one(),
        "duplicate_names": session.execute(text("""
            SELECT count(*) FROM (
                SELECT name_nexus FROM professors WHERE name_nexus IS NOT NULL
                GROUP BY name_nexus HAVING count(*) > 1
            ) d
        """)).scalar_one(),
    }
    for table, column in REFERENCING_COLUMNS:
        stats[table] = session.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()
    stats["top_names"] = [
        tuple(r) for r in session.execute(text(f"""
            SELECT p.name_nexus, count(*) AS n FROM professors p WHERE {pred}
            GROUP BY p.name_nexus ORDER BY n DESC, p.name_nexus LIMIT :n
        """), {"n": sample_size})
    ]
    stats["sample"] = [
        tuple(r) for r in session.execute(text(f"""
            SELECT p.id, p.name_nexus, p.department FROM professors p WHERE {pred}
            ORDER BY random() LIMIT :n
        """), {"n": sample_size})
    ]
    return stats


def delete_orphans(session: Session, batch_size: int = DEFAULT_BATCH_SIZE) -> int:
    """Delete deletable rows in batches, one committed transaction per batch.

    Returns the number of rows deleted.
    """
    pred = _orphan_predicate("p")
    lock_sql = text(f"""
        SELECT p.id FROM professors p WHERE p.id > :after AND {pred}
        ORDER BY p.id LIMIT :batch FOR UPDATE OF p SKIP LOCKED
    """)
    # A new statement takes a new snapshot, so this re-check sees references
    # committed after the candidates were picked. The row locks taken above
    # stop new references to these rows until the batch commits.
    delete_sql = text(f"""
        DELETE FROM professors p WHERE p.id = ANY(:ids) AND {pred} RETURNING p.id
    """)

    total = 0
    batch_no = 0
    retries = 0
    after = 0
    while True:
        started = time.monotonic()
        ids = list(session.execute(lock_sql, {"after": after, "batch": batch_size}).scalars())
        if not ids:
            session.commit()
            break
        try:
            deleted = len(session.execute(delete_sql, {"ids": ids}).all())
            session.commit()
        except IntegrityError:
            # A reference slipped in between the re-check and the FK check.
            # Nothing in this batch was deleted; pick the candidates again.
            session.rollback()
            retries += 1
            if retries > 3:
                raise
            logger.warning("Batch hit a foreign key violation; retrying")
            continue
        retries = 0
        batch_no += 1
        total += deleted
        after = ids[-1]
        logger.info(
            "Batch %d: deleted %d of %d candidates (ids %d-%d) in %.1fs, %d total",
            batch_no, deleted, len(ids), ids[0], ids[-1], time.monotonic() - started, total,
        )
    return total


def _print_stats(stats: dict) -> None:
    logger.info("professors: %d rows, %d distinct name_nexus, %d names duplicated",
                stats["professors"], stats["distinct_name_nexus"], stats["duplicate_names"])
    for table, _ in REFERENCING_COLUMNS:
        logger.info("%s: %d rows", table, stats[table])
    logger.info("deletable orphan rows: %d (%d would remain)",
                stats["deletable"], stats["professors"] - stats["deletable"])
    if stats["top_names"]:
        logger.info("most-duplicated names (rows to delete):")
        for name, n in stats["top_names"]:
            logger.info("  %-40s %d", name, n)
    if stats["sample"]:
        logger.info("random sample of rows to delete:")
        for pid, name, dept in stats["sample"]:
            logger.info("  id=%-7d %-40s %s", pid, name, dept)


def run(session: Session, *, apply: bool, batch_size: int = DEFAULT_BATCH_SIZE) -> dict:
    """Print what would be deleted and, with ``apply``, delete it.

    Returns ``{"before": stats, "after": stats | None, "deleted": int, "seconds": float}``.
    """
    check_schema(session)
    before = collect_stats(session)
    session.commit()  # end the read transaction; nothing was written
    _print_stats(before)

    if not apply:
        logger.info("Dry run: nothing deleted. Re-run with --apply to delete.")
        return {"before": before, "after": None, "deleted": 0, "seconds": 0.0}

    started = time.monotonic()
    deleted = delete_orphans(session, batch_size=batch_size)
    elapsed = time.monotonic() - started

    after = collect_stats(session, sample_size=0)
    session.commit()
    logger.info("Deleted %d rows in %.1fs. professors: %d -> %d",
                deleted, elapsed, before["professors"], after["professors"])
    for table, _ in REFERENCING_COLUMNS:
        if after[table] != before[table]:
            logger.warning("%s changed during the run: %d -> %d "
                           "(expected only if another job wrote to it)",
                           table, before[table], after[table])
    logger.info("Remaining deletable rows: %d", after["deletable"])
    return {"before": before, "after": after, "deleted": deleted, "seconds": elapsed}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--apply", action="store_true",
                        help="Delete the rows. Without this flag nothing is changed.")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE,
                        help=f"Rows per transaction (default {DEFAULT_BATCH_SIZE}).")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    from dotenv import load_dotenv
    load_dotenv()
    from db.connection import get_engine

    engine = get_engine()
    logger.info("Target: %s", engine.url.render_as_string(hide_password=True))
    with Session(engine) as session:
        run(session, apply=args.apply, batch_size=args.batch_size)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""add uq_gaucho_score_pair unique constraint

Revision ID: 9acf49a4b131
Revises: c4a8e1b0f2d3
Create Date: 2026-09-28 00:00:00.000000

``db/models.py`` has declared ``UniqueConstraint("professor_id", "course_id",
name="uq_gaucho_score_pair")`` on ``gaucho_scores`` since the first release,
and the test suite (which builds its schema with ``Base.metadata.create_all``)
relies on it, but no migration ever created it. Production and any database
built with ``alembic upgrade head`` therefore lack it.

This revision is safe to run from any of the states we know about:

* a fresh database migrated revision by revision,
* production, which is stamped ``3ee0c9e2add3`` but already has the
  ``scheduled_sections`` table (``1fd97b94581d`` and ``c4a8e1b0f2d3`` are
  already idempotent for that, so a plain ``alembic upgrade head`` walks
  straight through them), and
* a database where the constraint, or a unique index of the same name, was
  already created by hand or by ``create_all``.

It refuses to run, and names the offending rows, if duplicate
``(professor_id, course_id)`` pairs exist. Deleting scores is a data decision
for a human, not for a deploy hook. Because Alembic runs the whole upgrade in
one transaction on PostgreSQL, a refusal also rolls back the index creation of
the earlier revisions in the same run, so the database is left untouched.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "9acf49a4b131"
down_revision: Union[str, Sequence[str], None] = "c4a8e1b0f2d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "gaucho_scores"
NAME = "uq_gaucho_score_pair"
COLUMNS = ("professor_id", "course_id")


def _constraint_exists(bind) -> bool:
    return bool(
        bind.execute(
            sa.text(
                "SELECT 1 FROM pg_constraint "
                "WHERE conname = :name AND conrelid = CAST(:tbl AS regclass)"
            ),
            {"name": NAME, "tbl": TABLE},
        ).scalar()
    )


def _unique_index_exists(bind) -> bool:
    return bool(
        bind.execute(
            sa.text(
                "SELECT 1 FROM pg_index i "
                "JOIN pg_class c ON c.oid = i.indexrelid "
                "WHERE c.relname = :name AND i.indrelid = CAST(:tbl AS regclass) "
                "AND i.indisunique"
            ),
            {"name": NAME, "tbl": TABLE},
        ).scalar()
    )


def _assert_no_duplicates(bind) -> None:
    dupes = bind.execute(
        sa.text(
            "SELECT professor_id, course_id, count(*) AS n "
            "FROM gaucho_scores GROUP BY professor_id, course_id "
            "HAVING count(*) > 1 ORDER BY n DESC, professor_id, course_id"
        )
    ).all()
    if dupes:
        sample = ", ".join(
            f"(professor_id={p}, course_id={c}) x{n}" for p, c, n in dupes[:10]
        )
        raise RuntimeError(
            f"Cannot add {NAME}: {len(dupes)} duplicate (professor_id, course_id) "
            f"pair(s) in {TABLE}, e.g. {sample}. Nothing was changed. Keep the "
            "newest row per pair (see docs/runbooks/reconcile-production-schema.md) "
            "and re-run the migration."
        )


def upgrade() -> None:
    bind = op.get_bind()
    if _constraint_exists(bind):
        return

    _assert_no_duplicates(bind)

    if _unique_index_exists(bind):
        # Someone already built the unique index by hand; adopt it rather than
        # building a second copy.
        op.execute(
            f"ALTER TABLE {TABLE} ADD CONSTRAINT {NAME} UNIQUE USING INDEX {NAME}"
        )
    else:
        op.create_unique_constraint(NAME, TABLE, list(COLUMNS))


def downgrade() -> None:
    op.execute(f"ALTER TABLE {TABLE} DROP CONSTRAINT IF EXISTS {NAME}")

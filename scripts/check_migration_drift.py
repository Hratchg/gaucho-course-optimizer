"""Report whether a database's schema has drifted from the repo's migrations.

Render doesn't run ``preDeployCommand`` for this service (see section 6 of
docs/runbooks/reconcile-production-schema.md), so a migration merged to master
reaches production only when someone runs ``alembic upgrade head`` by hand.
Until 2026-09-29 production sat three revisions behind and nobody noticed.
This check notices:

* **Revision:** the database's ``alembic_version`` is not the repo's head.
  Either migrations are waiting to be applied, or the database is stamped
  with a revision this checkout doesn't have.
* **Schema:** alembic's ``compare_metadata`` finds a difference between the
  models and the live tables, indexes and constraints, for example one made
  or dropped by hand.

It only reads: the session is opened with ``default_transaction_read_only``.
A Neon ``-pooler`` host is rewritten to the direct one, so that setting belongs
to a real session instead of relying on the pooler (PgBouncer, transaction
mode) to carry startup options over to whichever server connection it hands out.

Usage:
    DATABASE_URL=... python scripts/check_migration_drift.py [--report FILE] [--run-url URL]

Exit status: 0 when in sync, 1 when drift was found (the report says what),
2 when the check couldn't run.
"""

import argparse
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from db.models import Base  # noqa: E402

RUNBOOK = "docs/runbooks/reconcile-production-schema.md"


@dataclass
class DriftReport:
    database_revisions: list[str]
    repo_heads: list[str]
    pending: list[str] = field(default_factory=list)  # "rev: message", oldest first
    unknown: list[str] = field(default_factory=list)  # database revisions the repo lacks
    schema_diffs: list[str] = field(default_factory=list)

    @property
    def in_sync(self) -> bool:
        return (
            sorted(self.database_revisions) == sorted(self.repo_heads)
            and not self.schema_diffs
        )


def direct_url(url: str) -> str:
    """The same URL with a Neon pooler host ("ep-x-pooler.…") swapped for the direct one."""
    parsed = make_url(url)
    host = parsed.host or ""
    first, dot, rest = host.partition(".")
    if first.endswith("-pooler"):
        parsed = parsed.set(host=first.removesuffix("-pooler") + dot + rest)
    return parsed.render_as_string(hide_password=False)


def read_only_engine(url: str):
    return create_engine(
        direct_url(url),
        connect_args={"options": "-c default_transaction_read_only=on"},
    )


def _script() -> ScriptDirectory:
    cfg = Config()
    cfg.set_main_option("script_location", str(ROOT / "db" / "migrations"))
    return ScriptDirectory.from_config(cfg)


def _ancestors(script: ScriptDirectory, revisions) -> set[str]:
    """The revisions and everything they were built on."""
    seen: set[str] = set()
    stack = list(revisions)
    while stack:
        rev = stack.pop()
        if rev in seen:
            continue
        seen.add(rev)
        down = script.get_revision(rev).down_revision
        stack.extend(down if isinstance(down, tuple) else [down] if down else [])
    return seen


def _describe(diff) -> list[str]:
    """One readable line per compare_metadata entry."""
    if isinstance(diff, list):  # column changes come grouped per column
        return [line for item in diff for line in _describe(item)]
    op, *args = diff
    if op.startswith("modify_"):
        _schema, table, column, _existing, old, new = args
        return [f"{op} {table}.{column}: {old!r} -> {new!r}"]
    if op in ("add_column", "remove_column"):
        _schema, table, column = args
        return [f"{op} {table}.{column.name}"]
    obj = args[0]
    table = getattr(obj, "table", None)
    on = f" on {table.name}" if table is not None else ""
    return [f"{op} {getattr(obj, 'name', None) or '(unnamed)'}{on}"]


def check(engine) -> DriftReport:
    script = _script()
    known = {rev.revision for rev in script.walk_revisions()}
    with engine.connect() as conn:
        context = MigrationContext.configure(conn)
        database = list(context.get_current_heads())
        diffs = compare_metadata(context, Base.metadata)
        conn.rollback()

    report = DriftReport(database_revisions=database, repo_heads=list(script.get_heads()))
    report.unknown = [rev for rev in database if rev not in known]
    applied = _ancestors(script, [rev for rev in database if rev in known])
    report.pending = [
        f"{rev.revision}: {rev.doc}"
        for rev in reversed(list(script.walk_revisions()))
        if rev.revision not in applied
    ]
    report.schema_diffs = [line for diff in diffs for line in _describe(diff)]
    return report


def render(report: DriftReport, run_url: str = "") -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "Production's schema doesn't match the migrations on master. This issue "
        "closes itself when the check passes again.",
        "",
        f"- **Database revision:** {', '.join(report.database_revisions) or 'none (no alembic_version row)'}",
        f"- **Repo head:** {', '.join(report.repo_heads)}",
        f"- **Last checked:** {now}",
    ]
    if run_url:
        lines.append(f"- **Last run:** {run_url}")
    if report.pending:
        lines += ["", "Migrations not applied yet, oldest first:", ""]
        lines += [f"- `{item}`" for item in report.pending]
    if report.unknown:
        lines += [
            "",
            "The database is stamped with revisions this checkout doesn't have "
            "(applied from an unmerged branch, or removed from the repo):",
            "",
        ]
        lines += [f"- `{rev}`" for rev in report.unknown]
    if report.schema_diffs:
        lines += ["", "Differences between the models and the live schema (`compare_metadata`):", ""]
        lines += [f"- `{item}`" for item in report.schema_diffs]
    lines += [
        "",
        f"To apply pending migrations, follow `{RUNBOOK}`: rehearse on a Neon branch, "
        "create a backup branch, then run `alembic upgrade head` against production.",
    ]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--report", help="write the drift report (markdown) to this file")
    parser.add_argument("--run-url", default="", help="link to this run, for the report")
    args = parser.parse_args(argv)

    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL is not set", file=sys.stderr)
        return 2
    engine = read_only_engine(url)
    try:
        report = check(engine)
    except Exception as exc:  # report the failure without echoing the URL
        print(f"Could not check {make_url(direct_url(url)).host}: {type(exc).__name__}: {exc}",
              file=sys.stderr)
        return 2
    finally:
        engine.dispose()

    if report.in_sync:
        print(f"In sync: database and repo are both at {', '.join(report.repo_heads)}; "
              "models match the schema.")
        return 0
    text = render(report, args.run_url)
    print(text)
    if args.report:
        Path(args.report).write_text(text)
    return 1


if __name__ == "__main__":
    sys.exit(main())

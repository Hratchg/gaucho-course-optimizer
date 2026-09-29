"""The scheduled drift check (scripts/check_migration_drift.py and its issue wrapper).

Each database test runs against its own scratch database (see
tests/test_migrations.py). The wrapper tests put a fake ``gh`` on PATH that
records its arguments, so no GitHub call is made.
"""
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest
from alembic import command
from sqlalchemy import text
from sqlalchemy.exc import InternalError

from scripts.check_migration_drift import (
    check,
    direct_url,
    main,
    read_only_engine,
    render,
)
from tests.test_migrations import BEFORE_UNIQUE, _config, _head, scratch_db  # noqa: F401

ROOT = Path(__file__).resolve().parent.parent
WRAPPER = ROOT / "scripts" / "migration_drift_check.sh"


def test_direct_url_drops_the_neon_pooler_suffix():
    pooled = "postgresql://u:secret@ep-cool-name-a1b2-pooler.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require"
    assert direct_url(pooled) == (
        "postgresql://u:secret@ep-cool-name-a1b2.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require"
    )
    local = "postgresql://gco:gco@localhost:5445/gco_test"
    assert direct_url(local) == local


def test_in_sync_at_head(scratch_db):
    command.upgrade(_config(), "head")
    report = check(read_only_engine(os.environ["DATABASE_URL"]))
    assert report.in_sync
    assert report.database_revisions == [_head()]
    assert (report.pending, report.unknown, report.schema_diffs) == ([], [], [])


def test_behind_lists_the_pending_migrations(scratch_db):
    command.upgrade(_config(), BEFORE_UNIQUE)
    report = check(read_only_engine(os.environ["DATABASE_URL"]))
    assert not report.in_sync
    assert [item.split(":")[0] for item in report.pending] == [_head()]
    # The model's unique constraint isn't in the database yet either.
    assert any("uq_gaucho_score_pair" in diff for diff in report.schema_diffs)


def test_no_alembic_version_is_drift(scratch_db):
    with scratch_db.begin() as conn:
        conn.execute(text("CREATE TABLE unrelated (id int)"))
    report = check(read_only_engine(os.environ["DATABASE_URL"]))
    assert not report.in_sync
    assert report.database_revisions == []
    assert len(report.pending) == 4
    assert "none (no alembic_version row)" in render(report)


def test_unknown_revision_is_drift(scratch_db):
    command.upgrade(_config(), "head")
    with scratch_db.begin() as conn:
        conn.execute(text("UPDATE alembic_version SET version_num = 'feedfacecafe'"))
    report = check(read_only_engine(os.environ["DATABASE_URL"]))
    assert not report.in_sync
    assert report.unknown == ["feedfacecafe"]
    assert "feedfacecafe" in render(report)


def test_hand_made_schema_change_is_drift(scratch_db):
    command.upgrade(_config(), "head")
    with scratch_db.begin() as conn:
        conn.execute(text("DROP INDEX ix_grade_distributions_course_id"))
        conn.execute(text("ALTER TABLE courses ADD COLUMN scratch text"))
    report = check(read_only_engine(os.environ["DATABASE_URL"]))
    assert not report.in_sync
    assert report.database_revisions == [_head()]
    assert "add_index ix_grade_distributions_course_id on grade_distributions" in report.schema_diffs
    assert "remove_column courses.scratch" in report.schema_diffs


def test_check_session_is_read_only(scratch_db):
    command.upgrade(_config(), "head")
    engine = read_only_engine(os.environ["DATABASE_URL"])
    with engine.connect() as conn:
        assert conn.execute(text("SHOW transaction_read_only")).scalar() == "on"
        with pytest.raises(InternalError, match="read-only"):
            conn.execute(text("DELETE FROM alembic_version"))
    engine.dispose()


def test_main_exit_codes_and_report(scratch_db, tmp_path, capsys):
    report_file = tmp_path / "report.md"
    command.upgrade(_config(), "head")
    assert main(["--report", str(report_file)]) == 0
    assert not report_file.exists()

    command.downgrade(_config(), BEFORE_UNIQUE)
    assert main(["--report", str(report_file), "--run-url", "https://example.test/run/1"]) == 1
    body = report_file.read_text()
    assert _head() in body and "https://example.test/run/1" in body


def test_main_cannot_check_without_leaking_the_password(monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:hunter2@127.0.0.1:1/nope?connect_timeout=2")
    assert main([]) == 2
    err = capsys.readouterr().err
    assert "127.0.0.1" in err and "hunter2" not in err


# --- the issue wrapper -------------------------------------------------------

def _fake_tools(tmp_path, open_issue="", check_exit=0, report="drift report\n"):
    """A gh that logs its arguments, and a python that stands in for the check."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "gh.log"
    (bin_dir / "gh").write_text(
        "#!/usr/bin/env bash\n"
        f'echo "$*" >> "{log}"\n'
        f'if [ "$1 $2" = "issue list" ]; then echo "{open_issue}"; fi\n'
    )
    # The fake check writes the report only for drift (exit 1 with --report).
    (bin_dir / "fakepython").write_text(
        "#!/usr/bin/env bash\n"
        f'if [ {check_exit} -eq 1 ] && [ -n "{report.strip()}" ]; then printf "%s" "{report}" > "$3"; fi\n'
        f"exit {check_exit}\n"
    )
    for tool in ("gh", "fakepython"):
        path = bin_dir / tool
        path.chmod(path.stat().st_mode | stat.S_IEXEC)
    env = {
        **os.environ,
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "PYTHON": str(bin_dir / "fakepython"),
        "DATABASE_URL": "postgresql://unused",
    }
    return env, log


def _run_wrapper(env):
    return subprocess.run(["bash", str(WRAPPER)], env=env, capture_output=True, text=True)


def _gh_calls(log):
    return log.read_text().splitlines() if log.exists() else []


def test_wrapper_opens_one_issue_on_drift(tmp_path):
    env, log = _fake_tools(tmp_path, check_exit=1)
    assert _run_wrapper(env).returncode == 0
    calls = _gh_calls(log)
    assert calls[0].startswith("issue list --label migration-drift --state open")
    assert any(c.startswith("label create migration-drift") for c in calls)
    assert any(c.startswith("issue create --title Production schema has drifted") for c in calls)


def test_wrapper_refreshes_the_open_issue_quietly(tmp_path):
    env, log = _fake_tools(tmp_path, open_issue="42", check_exit=1)
    assert _run_wrapper(env).returncode == 0
    calls = _gh_calls(log)
    assert any(c.startswith("issue edit 42 --body-file") for c in calls)
    assert not any(c.startswith(("issue create", "issue comment")) for c in calls)


def test_wrapper_closes_the_issue_when_back_in_sync(tmp_path):
    env, log = _fake_tools(tmp_path, open_issue="42", check_exit=0)
    assert _run_wrapper(env).returncode == 0
    calls = _gh_calls(log)
    assert any(c.startswith("issue comment 42 --body In sync again") for c in calls)
    assert "issue close 42" in calls


def test_wrapper_does_nothing_when_in_sync(tmp_path):
    env, log = _fake_tools(tmp_path, check_exit=0)
    assert _run_wrapper(env).returncode == 0
    assert [c.split(" --")[0] for c in _gh_calls(log)] == ["issue list"]


@pytest.mark.parametrize("check_exit, report", [(2, ""), (1, "")])
def test_wrapper_fails_and_leaves_issues_alone_when_the_check_cannot_run(tmp_path, check_exit, report):
    """Exit 2, or exit 1 with no report (a Python crash), is not drift."""
    env, log = _fake_tools(tmp_path, open_issue="42", check_exit=check_exit, report=report)
    result = _run_wrapper(env)
    assert result.returncode == 1
    assert "could not run" in result.stdout
    assert _gh_calls(log) == []


def test_script_runs_from_the_command_line(scratch_db):
    """The workflow calls the file directly, so its imports must work from any cwd."""
    command.upgrade(_config(), "head")
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_migration_drift.py")],
        env=os.environ.copy(), cwd="/", capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "In sync" in result.stdout

"""Alembic migrations must build the schema the models describe.

The rest of the suite builds its schema with ``Base.metadata.create_all``, so
without this file a constraint or index could exist only in the models (or only
in the migrations) and nothing would notice. That is how production ended up
without ``uq_gaucho_score_pair``. Each test runs against its own scratch
database on the same server as ``DATABASE_URL``.
"""
import os
import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

from db.models import Base

ROOT = Path(__file__).resolve().parent.parent
INITIAL = "3ee0c9e2add3"
BEFORE_UNIQUE = "c4a8e1b0f2d3"

# scheduled_sections exactly as production has it: created outside Alembic,
# with its unique constraint and FKs but none of the ix_* lookup indexes.
PRODUCTION_SCHEDULED_SECTIONS = """
CREATE TABLE scheduled_sections (
    id SERIAL PRIMARY KEY,
    professor_id INTEGER REFERENCES professors(id),
    course_id INTEGER REFERENCES courses(id),
    quarter_code TEXT NOT NULL,
    quarter_name TEXT,
    enroll_code TEXT NOT NULL,
    instructor_name_raw TEXT,
    days TEXT,
    begin_time TEXT,
    end_time TEXT,
    building TEXT,
    room TEXT,
    enrolled INTEGER,
    max_enroll INTEGER,
    section_cancelled BOOLEAN,
    fetched_at TIMESTAMP WITHOUT TIME ZONE,
    CONSTRAINT uq_scheduled_section_quarter_enroll UNIQUE (quarter_code, enroll_code)
)
"""


@pytest.fixture
def scratch_db(monkeypatch):
    """Create an empty database, point DATABASE_URL (and so env.py) at it."""
    base_url = make_url(os.environ["DATABASE_URL"])
    name = f"{base_url.database}_mig_{uuid.uuid4().hex[:8]}"
    admin = create_engine(base_url, isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as conn:
            conn.execute(text(f'CREATE DATABASE "{name}"'))
    except Exception as exc:  # no CREATEDB privilege, e.g. a hosted DB
        admin.dispose()
        pytest.skip(f"cannot create a scratch database: {exc}")

    url = base_url.set(database=name)
    monkeypatch.setenv("DATABASE_URL", url.render_as_string(hide_password=False))
    engine = create_engine(url)
    try:
        yield engine
    finally:
        engine.dispose()
        with admin.connect() as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        admin.dispose()


def _config() -> Config:
    # No ini file: env.py would otherwise run logging.fileConfig and disable the
    # loggers other tests capture.
    cfg = Config()
    cfg.set_main_option("script_location", str(ROOT / "db" / "migrations"))
    return cfg


def _head() -> str:
    return ScriptDirectory.from_config(_config()).get_current_head()


def _current(engine) -> str:
    with engine.connect() as conn:
        return MigrationContext.configure(conn).get_current_revision()


def _diff(engine):
    with engine.connect() as conn:
        return compare_metadata(MigrationContext.configure(conn), Base.metadata)


def test_upgrade_head_matches_models(scratch_db):
    command.upgrade(_config(), "head")
    assert _current(scratch_db) == _head()
    assert _diff(scratch_db) == []


def test_upgrade_head_twice_is_a_noop(scratch_db):
    command.upgrade(_config(), "head")
    before = inspect(scratch_db)
    indexes = {t: before.get_indexes(t) for t in before.get_table_names()}
    command.upgrade(_config(), "head")
    after = inspect(scratch_db)
    assert {t: after.get_indexes(t) for t in after.get_table_names()} == indexes
    assert _current(scratch_db) == _head()


def test_upgrade_from_production_state(scratch_db):
    """Stamped at the initial revision, scheduled_sections built by hand."""
    command.upgrade(_config(), INITIAL)
    with scratch_db.begin() as conn:
        conn.execute(text(PRODUCTION_SCHEDULED_SECTIONS))
        conn.execute(text("INSERT INTO courses (id, code) VALUES (1, 'CMPSC 8')"))
        conn.execute(text("INSERT INTO professors (id, name_nexus) VALUES (1, 'DOE J')"))
        conn.execute(text(
            "INSERT INTO scheduled_sections (course_id, professor_id, quarter_code, enroll_code) "
            "VALUES (1, 1, '20264', '12345')"
        ))
        conn.execute(text(
            "INSERT INTO gaucho_scores (professor_id, course_id, score) VALUES (1, 1, 80)"
        ))

    command.upgrade(_config(), "head")

    assert _current(scratch_db) == _head()
    assert _diff(scratch_db) == []
    with scratch_db.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM scheduled_sections")).scalar() == 1
        assert conn.execute(text("SELECT count(*) FROM gaucho_scores")).scalar() == 1


def test_unique_pair_refuses_duplicates_and_changes_nothing(scratch_db):
    command.upgrade(_config(), INITIAL)
    with scratch_db.begin() as conn:
        conn.execute(text("INSERT INTO courses (id, code) VALUES (1, 'CMPSC 8')"))
        conn.execute(text("INSERT INTO professors (id, name_nexus) VALUES (1, 'DOE J')"))
        conn.execute(text(
            "INSERT INTO gaucho_scores (professor_id, course_id, score) "
            "VALUES (1, 1, 80), (1, 1, 81)"
        ))

    with pytest.raises(RuntimeError, match="duplicate"):
        command.upgrade(_config(), "head")

    # One transaction for the whole run: the earlier revisions rolled back too.
    assert _current(scratch_db) == INITIAL
    insp = inspect(scratch_db)
    assert "scheduled_sections" not in insp.get_table_names()
    assert insp.get_indexes("gaucho_scores") == []
    with scratch_db.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM gaucho_scores")).scalar() == 2


def test_unique_pair_downgrade_and_reapply(scratch_db):
    command.upgrade(_config(), "head")
    command.downgrade(_config(), BEFORE_UNIQUE)
    names = {u["name"] for u in inspect(scratch_db).get_unique_constraints("gaucho_scores")}
    assert "uq_gaucho_score_pair" not in names
    command.upgrade(_config(), "head")
    assert _diff(scratch_db) == []


def test_unique_pair_adopts_a_hand_built_index(scratch_db):
    command.upgrade(_config(), BEFORE_UNIQUE)
    with scratch_db.begin() as conn:
        conn.execute(text(
            "CREATE UNIQUE INDEX uq_gaucho_score_pair ON gaucho_scores (professor_id, course_id)"
        ))
    command.upgrade(_config(), "head")
    assert _diff(scratch_db) == []

# Plan 01-01: Infrastructure Bug Fixes — Summary

**Phase:** 01-foundation-bug-fixes
**Plan:** 01-01
**Executed:** 2026-03-30
**Status:** Complete

## What Was Implemented

### Task 1: Connection Pool + SessionLocal Factory (FDN-02)
- `db/connection.py`: Added `pool_size=5, max_overflow=10, pool_recycle=1800, pool_pre_ping=True` to `create_engine()`
- Added `get_session_local()` singleton factory with double-checked locking (`threading.Lock`) to prevent cold-start deadlock
- `get_session()` backward-compatible — delegates to `get_session_local()`
- Phase 2 FastAPI usage: `from db.connection import get_session_local`

### Task 2: FK Indexes + RMP Auth Token (FDN-04, FDN-05)
- `db/migrations/versions/1fd97b94581d_add_fk_indexes.py`: New Alembic migration, `down_revision='3ee0c9e2add3'`, 6 `create_index` + 6 `drop_index` calls covering: `grade_distributions.professor_id`, `grade_distributions.course_id`, `rmp_ratings.professor_id`, `rmp_comments.rmp_rating_id`, `gaucho_scores.professor_id`, `gaucho_scores.course_id`
- `scrapers/rmp_scraper.py`: Hardcoded token `dGVzdDp0ZXN0` removed; `auth_token: str | None = None`; `os.environ["RMP_AUTH_TOKEN"]` with no fallback (fail-loud per FDN-05)

### D-07 Finding: VADER Caching Already Satisfied
`etl/nlp_processor.py` already has `_sia = None` module-level singleton and `_get_sia()` lazy-init. No code change needed — D-07 is satisfied as-is.

### .env.example
Already contained `DATABASE_URL=` and `RMP_AUTH_TOKEN=` from initial scaffold — no change required.

## Tests
- `tests/test_db_connection.py`: 4 pass — engine, session, session_local singleton, cold-start (no deadlock)
- `tests/test_rmp_scraper.py`: 3 pass — parse, school_id (explicit auth_token), name search

## Requirements Covered
- FDN-02: Connection pool configured ✓
- FDN-04: FK indexes in Alembic migration ✓
- FDN-05: No hardcoded credentials ✓

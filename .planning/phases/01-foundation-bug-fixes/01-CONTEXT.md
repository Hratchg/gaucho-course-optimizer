# Phase 1: Foundation & Bug Fixes - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix the three critical infrastructure bugs that would make the future API unacceptably slow or broken (N+1 query, missing connection pool, missing DB indexes), secure credentials, verify the full ETL pipeline runs end-to-end on Neon PostgreSQL, and add automated tests for pipeline and scoring logic. No UI work. No FastAPI work. Foundation only.

</domain>

<decisions>
## Implementation Decisions

### N+1 Fix Location
- **D-01:** Fix the N+1 in `dashboard/queries.py` directly — patch the existing Streamlit file so the prototype continues to work correctly during Phase 2 development. Do not leave Streamlit broken.
- **D-02:** Connection pool configuration lives in `db/connection.py` only (the shared engine factory). FastAPI's `dependencies.py` in Phase 2 will import `SessionLocal` from there — one fix covers both services.

### Neon Database Seeding
- **D-03:** Restore the Neon database from `data/gco_dump.sql` (existing 13 MB dump). Fast — data is already scraped and scored. Use `pg_restore` to load into Neon. Verify connection and that `GauchoScore` records are present after restore.
- **D-04:** Set up a weekly automated pg_dump as a GitHub Action that dumps Neon DB to a repo artifact. Protects against accidental data loss during active development.

### Scraper Test Mocking
- **D-05:** Retrofit mocking on ALL existing scraper tests that make real HTTP calls (`test_rmp_scraper.py`, `test_targeted_scrape.py`, any other file hitting RMP GraphQL or Daily Nexus). Use `pytest-mock`'s `mocker` fixture to patch `requests.Session.send` or equivalent. CI must be fully deterministic — no real external HTTP calls.
- **D-06:** Expand `tests/fixtures/` JSON files for mock data (matches the existing pattern — `rmp_graphql_response.json` and `rmp_name_search_response.json` already exist there). Do not put mock payloads inline in test functions.

### VADER Caching
- **D-07:** Fix VADER caching in Phase 1 — instantiate `SentimentIntensityAnalyzer()` once at module load in `etl/nlp_processor.py` (or use `functools.lru_cache`), not per call. One-line fix; speeds up pipeline verification and all future batch runs.

### Claude's Discretion
- Alembic migration strategy for DB indexes: create a new Alembic migration in `db/migrations/versions/` (Alembic is already configured — `env.py` and initial schema migration both exist). Do NOT use `__table_args__` + re-run `create_all` on existing DB.
- Connection pool values: `pool_size=5, max_overflow=10, pool_recycle=1800, pool_pre_ping=True` (Render free tier has ~25 connection limit; FastAPI threadpool defaults to 40 workers — conservative pool prevents exhaustion).
- RMP auth token migration: move from hardcoded fallback in `scrapers/rmp_scraper.py:105` to `os.environ["RMP_AUTH_TOKEN"]` with no default (fail loudly if unset). Use `pydantic-settings` pattern introduced in Phase 2 as the longer-term fix.
- Cascade delete rules: defer to a separate concern — not required for Phase 1 correctness.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Requirements
- `.planning/REQUIREMENTS.md` §Foundation & Bug Fixes — FDN-01..06, TEST-01..02

### Existing Code to Fix
- `db/connection.py` — Add pool_size, max_overflow, pool_recycle, pool_pre_ping; export SessionLocal
- `dashboard/queries.py:43-86` — N+1 bug: fix get_professors_for_course() with single JOIN
- `scrapers/rmp_scraper.py:105` — Hardcoded auth token: move to env var, no default
- `etl/nlp_processor.py` — VADER analyzer rebuilt per call: instantiate once at module load
- `db/models.py` — No indexes on foreign keys: add via new Alembic migration
- `db/migrations/versions/` — Existing migration: add new migration file for indexes

### Test Infrastructure
- `tests/conftest.py` — SAVEPOINT pattern: use for all new DB tests
- `tests/fixtures/` — Existing JSON fixtures: expand here (do not put mock data inline in tests)

### Research
- `.planning/research/PITFALLS.md` — Pitfalls 2, 3, 4, 9, 12 directly apply to Phase 1 work
- `.planning/research/STACK.md` §Database — Neon connection string format, sslmode=require, pool_pre_ping

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tests/conftest.py` `db_session` fixture (SAVEPOINT pattern) — all new DB integration tests should use this fixture
- `tests/fixtures/rmp_graphql_response.json`, `rmp_name_search_response.json` — expand with additional fixture payloads for targeted scrape mocking
- `data/gco_dump.sql` (13 MB) — use for Neon seeding via pg_restore

### Established Patterns
- **Function-based tests with inline data creation:** Codebase uses `db_session.add(Professor(...)); db_session.flush()` — no factory classes. New tests should follow the same pattern.
- **pytest-mock is installed but rarely used:** `pytest-mock` 3.14.x is in `requirements-dev.txt`; existing scraper tests don't use it yet. Phase 1 retrofits this for all HTTP-calling tests.
- **Session commits are production-safe in tests:** SAVEPOINT pattern means tests can call `session.commit()` freely — the outer transaction rolls back after each test.

### Integration Points
- `db/connection.py` `get_engine()` / `SessionLocal` — central session factory; pool fix must land here
- `db/migrations/env.py` — Alembic env already configured; new index migration adds to `versions/`
- `tests/conftest.py` — shared test fixtures; any new shared fixtures belong here

</code_context>

<specifics>
## Specific Ideas

- Neon connection string requires `?sslmode=require` parameter — must be included in `DATABASE_URL` env var
- Weekly pg_dump GitHub Action: run `pg_dump $DATABASE_URL > data/gco_dump.sql` and commit or upload as artifact
- For N+1 fix in `dashboard/queries.py`: use SQLAlchemy `joinedload()` or rewrite as single query with explicit JOINs — do NOT just move the per-professor loop to a different location
- After Neon restore, run `SELECT COUNT(*) FROM gaucho_scores` to confirm data is present and scores are valid

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within Phase 1 scope.

</deferred>

---

*Phase: 01-foundation-bug-fixes*
*Context gathered: 2026-03-30*

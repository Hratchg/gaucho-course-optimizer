# Phase 1: Foundation & Bug Fixes - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-30
**Phase:** 01-foundation-bug-fixes
**Areas discussed:** N+1 fix scope, Neon seeding strategy, Scraper test mocking scope, VADER caching

---

## N+1 Fix Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Fix dashboard/queries.py | Patch existing Streamlit file so prototype stays correct during Phase 2 development | ✓ |
| Skip Streamlit, write JOIN as standalone module | Write replacement query in db/ or etl/ for Phase 2; don't touch Streamlit | |
| Just document, fix in Phase 2 FastAPI | Accept Streamlit stays slow; don't fix N+1 until FastAPI routes are written | |

**User's choice:** Fix dashboard/queries.py (Recommended)
**Notes:** Keep Streamlit working during Phase 2 development.

---

## Connection Pool Config Location

| Option | Description | Selected |
|--------|-------------|----------|
| db/connection.py only | Fix the shared engine factory — FastAPI imports from there in Phase 2 | ✓ |
| Separate configs per service | Keep Streamlit and FastAPI pool configs separate for independent tuning | |

**User's choice:** db/connection.py only (Recommended)
**Notes:** One fix covers both Streamlit and future FastAPI.

---

## Neon Seeding Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Restore from dump | pg_restore data/gco_dump.sql into Neon — fast, data already scraped and scored | ✓ |
| Run pipeline from scratch | Full scrape → match → NLP → score against empty Neon DB | |
| Both: restore + smoke-test pipeline | Restore dump, then run one incremental pipeline step to verify writes work | |

**User's choice:** Restore from dump (Recommended)
**Notes:** 13 MB dump already exists with valid scored data.

---

## Automated DB Backup

| Option | Description | Selected |
|--------|-------------|----------|
| Set up weekly backup | GitHub Action: dump Neon DB weekly to repo artifact | ✓ |
| One-time only | Use existing dump for seeding; manage backups manually later | |

**User's choice:** Set up weekly backup (Recommended)
**Notes:** Protects against data loss during active development.

---

## Scraper Test Mocking Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Retrofit all existing scraper tests | Add pytest-mock patches to all HTTP-calling test files — fully deterministic CI | ✓ |
| New tests only — mark existing as integration | @pytest.mark.integration on existing HTTP tests, exclude from CI | |

**User's choice:** Retrofit all existing scraper tests (Recommended)

---

## Mock Data Storage

| Option | Description | Selected |
|--------|-------------|----------|
| Expand fixture files | Add JSON files to tests/fixtures/ — matches existing pattern | ✓ |
| Inline in test functions | Define mock return values inside test code | |

**User's choice:** Expand fixture files (Recommended)
**Notes:** rmp_graphql_response.json and rmp_name_search_response.json already exist as examples.

---

## VADER Caching

| Option | Description | Selected |
|--------|-------------|----------|
| Fix in Phase 1 | Instantiate SentimentIntensityAnalyzer() once at module load — one-line fix | ✓ |
| Defer to later | Low urgency for batch pipeline; fix after Phase 3 | |

**User's choice:** Fix in Phase 1 (Recommended)
**Notes:** ~5 min effort; speeds up pipeline verification run immediately.

---

## Claude's Discretion

- Alembic migration for DB indexes (not __table_args__ + create_all on existing DB)
- Connection pool values: pool_size=5, max_overflow=10, pool_recycle=1800, pool_pre_ping=True
- RMP token migration to os.environ["RMP_AUTH_TOKEN"] with no default
- Cascade deletes deferred

## Deferred Ideas

None raised during discussion.

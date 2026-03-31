# Phase 2: FastAPI Backend - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-31
**Phase:** 02-fastapi-backend
**Areas discussed:** Score computation strategy, N+1 rewrite scope, FastAPI app layout, Test DB strategy

---

## Score Computation Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Compute fresh per-request | Use dashboard/queries.py + etl/scoring.py to compute factors and score live on each request. No migration needed. | ✓ |
| Store factors in DB | Add gpa_factor etc. columns to gaucho_scores via Alembic migration. ETL populates them. API reads from DB. | |
| Hybrid: read score from DB, factors from query | Read pre-computed score from gaucho_scores, but run a JOIN to get raw stats for factor values separately. | |

**User's choice:** Compute fresh per-request

---

### Score computation follow-up: weight parameters

| Option | Description | Selected |
|--------|-------------|----------|
| Return default score + raw factors only | API returns default-weight score + raw factors. Phase 3 sliders recompute client-side. No server round-trip on weight change. | ✓ |
| Accept optional weight query params | API accepts ?gpa_weight=0.4 etc. API computes and returns custom score. Weight slider changes require API call. | |

**User's choice:** Return default score + raw factors only

---

## N+1 Rewrite Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Include as Phase 2 Plan 1 | Single isolated plan: rewrite compute_all_scores() with bulk JOIN, confirm pipeline works, then build API. Closes FDN-03. | ✓ |
| Defer — start API directly | API doesn't call compute_all_scores(). Current 11,750 records sufficient. Fix pipeline separately. | |

**User's choice:** Include as Phase 2 Plan 1

---

## FastAPI App Layout

| Option | Description | Selected |
|--------|-------------|----------|
| api/ package with routers | api/main.py, api/dependencies.py, api/routers/health.py, api/routers/courses.py, api/routers/professors.py | ✓ |
| Flat api/main.py | Single file with all 5 routes inline | |

**User's choice:** api/ package with routers

---

## Test DB Strategy

**Context provided:** User asked which approach is best for production-ready/shipping to active users. 
**Clarification:** SQLite in-memory was ruled out because existing queries use PostgreSQL-specific features (func.stddev(), ilike, nullslast, JSON columns) that SQLite doesn't support. Real PostgreSQL in CI is required for production confidence.

| Option | Description | Selected |
|--------|-------------|----------|
| GitHub Actions PostgreSQL service container | CI spins up postgres:15 container. No external credentials. Free. SAVEPOINT pattern unchanged. | ✓ |
| Neon test branch | Second Neon database branch. TEST_DATABASE_URL as CI secret. Identical to production. | |
| SQLite in-memory | Fastest, zero setup, but fails on PostgreSQL-specific query features. | |

**User's choice:** GitHub Actions PostgreSQL service container

### Test session injection follow-up

| Option | Description | Selected |
|--------|-------------|----------|
| dependency_overrides on get_db | app.dependency_overrides[get_db] = lambda: yield db_session. Standard FastAPI pattern. | ✓ |
| Separate test app factory | test_app.py builds FastAPI app with hardwired test session. More isolated, more boilerplate. | |

**User's choice:** dependency_overrides on get_db

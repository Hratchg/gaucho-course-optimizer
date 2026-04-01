---
phase: 02-fastapi-backend
plan: 05
subsystem: testing
tags: [pytest, fastapi, sqlalchemy, savepoint, dependency-injection, testclient]

requires:
  - phase: 02-02
    provides: FastAPI app, health endpoint, get_db dependency
  - phase: 02-03
    provides: courses router (search + professor ranking endpoints)
  - phase: 02-04
    provides: professors router (grades + comments endpoints)

provides:
  - tests/test_api/ package with client fixture using SAVEPOINT dependency injection
  - 13 endpoint tests covering all 5 API routes
  - VADER normalization integration test (avg_sentiment=0.0 → sentiment_factor=0.5)
  - Fixed GROUP BY bug in dashboard/queries.py (PostgreSQL strict mode compliance)

affects: [ci, testing, all future api phases]

tech-stack:
  added: []
  patterns: [SAVEPOINT db_session injection via app.dependency_overrides, TestClient fixture pattern]

key-files:
  created:
    - tests/test_api/__init__.py
    - tests/test_api/conftest.py
    - tests/test_api/test_health.py
    - tests/test_api/test_courses.py
    - tests/test_api/test_professors.py
  modified:
    - dashboard/queries.py

key-decisions:
  - "Used app.dependency_overrides[get_db] to inject SAVEPOINT session — no DATABASE_URL needed in tests"
  - "test_grades_requires_course_id uses client only (no seeded data) since 422 fires before DB access"
  - "Behaviors 5+6 (professor ranking list shape + field names) merged into one test function"

patterns-established:
  - "API endpoint tests: seed via db_session ORM fixture, call via TestClient, assert on real response data"
  - "404 sentinel: use ID 999999 for non-existent resource tests"
  - "Validation-only tests (422): do not seed data, just call endpoint with invalid params"

requirements-completed: [TEST-03, TEST-04]

duration: 45min
completed: 2026-03-31
---

# Plan 02-05: Wave 3 Endpoint Tests Summary

**13 FastAPI endpoint tests using SAVEPOINT dependency injection, covering all 5 routes with real PostgreSQL assertions**

## Performance

- **Duration:** ~45 min
- **Completed:** 2026-03-31
- **Tasks:** 2
- **Files modified:** 6 (5 created, 1 bugfix)

## Accomplishments

- Created `tests/test_api/` package with `client` fixture that injects the SAVEPOINT `db_session` into FastAPI via `dependency_overrides[get_db]` — no DATABASE_URL required in tests
- 13 endpoint tests across 3 files covering all 5 routes: health, course search (validation), professor ranking (shape + VADER normalization), grades (distribution + required param), comments (list + limit + 404s)
- Fixed GROUP BY bug in `dashboard/queries.py` — `sentiment_sq.c.avg_sentiment` was missing from the clause, causing PostgreSQL `GroupingError` on the professor ranking endpoint
- Full test suite: **129 tests pass, 0 failures**

## Task Commits

1. **Task 1: Create test_api/ package and client fixture** — `301593f` (feat)
2. **Task 2: Write endpoint tests for all five routes** — `4701f05` (feat + bugfix)
3. **Quality fix: Improve test quality in professors tests** — `604dc75` (fix)

## Files Created/Modified

- `tests/test_api/__init__.py` — empty package marker
- `tests/test_api/conftest.py` — `client` fixture: injects SAVEPOINT `db_session` via `app.dependency_overrides[get_db]`, clears overrides in teardown
- `tests/test_api/test_health.py` — 1 test: GET /health → `{"status": "ok"}`
- `tests/test_api/test_courses.py` — 6 tests: search results, special char 422, 101-char 422, professor ranking shape+fields, VADER normalization, course 404
- `tests/test_api/test_professors.py` — 6 tests: grades distribution, course_id required 422, grades 404, comments list, limit param, comments 404
- `dashboard/queries.py` — added `sentiment_sq.c.avg_sentiment` to GROUP BY clause (PostgreSQL strict compliance fix)

## Decisions Made

- Merged professor ranking shape (behavior 5) and field existence (behavior 6) into one test function `test_professors_returns_ranked_list` — both assertions belong together with no value from separating them
- `test_grades_requires_course_id` uses hardcoded `/professors/1/grades` with `client` only — FastAPI validates `course_id` before any DB access, so no seeded data is needed
- `test_comments_limit` asserts `1 <= len(data) <= 2` (not just `<= 2`) — lower bound prevents masking bugs where 0 results would silently pass

## Deviations from Plan

### Auto-fixed Issues

**1. [GROUP BY Missing Column] PostgreSQL GroupingError in professor ranking endpoint**
- **Found during:** Task 2 (running `pytest tests/test_api/ -v`)
- **Issue:** `dashboard/queries.py` line 71 had `group_by(Professor.id, RmpRating.id)` but the SELECT includes `sentiment_sq.c.avg_sentiment` as a non-aggregated column — PostgreSQL strict mode raises `GroupingError`
- **Fix:** Added `sentiment_sq.c.avg_sentiment` to the `group_by()` call; column is already a scalar per `(Professor, RmpRating)` pair from the subquery, so semantics unchanged
- **Files modified:** `dashboard/queries.py`
- **Verification:** `test_professors_returns_ranked_list` and `test_professors_sentiment_normalization` both pass; full suite 129 tests green
- **Committed in:** `4701f05`

---

**Total deviations:** 1 auto-fixed (bug in pre-existing production code surfaced by new tests)
**Impact on plan:** Fix required for tests to pass; minimal change, no scope creep.

## Issues Encountered

- GROUP BY PostgreSQL strict mode failure in `dashboard/queries.py` — the existing `get_professors_for_course()` query used a subquery column in SELECT without including it in GROUP BY. This was masked in SQLite (used for other tests) but enforced by PostgreSQL. Fixed with one-line addition.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- All 5 API endpoints have integration tests using real PostgreSQL sessions
- CI (`.github/workflows/test.yml`) already runs `pytest -v` with the postgres:16 service — TEST-04 satisfied without workflow changes
- Phase 2 FastAPI Backend is feature-complete: scoring engine, 5 routers, and full endpoint test coverage
- Ready for Phase 3 (frontend or deployment)

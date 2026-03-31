# Phase 2: FastAPI Backend - Context

**Gathered:** 2026-03-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Build five REST endpoints that expose course search, professor ranking (with raw scoring factors), grade history, comments, and health check. No UI work. No deployment. The API must be fully tested against a real PostgreSQL database so it is safe to ship to active users.

Also includes the deferred Phase 1 fix: rewrite `compute_all_scores()` in `etl/scoring.py` from a 3-queries-per-professor N+1 loop to a single bulk JOIN (addresses FDN-03).

</domain>

<decisions>
## Implementation Decisions

### Score Computation Strategy
- **D-01:** Compute Gaucho Score **fresh per-request** — do not read from the `gaucho_scores` table. The rankings endpoint (`GET /courses/{id}/professors`) calls `dashboard/queries.py:get_professors_for_course()` to fetch raw GPA/RMP/sentiment data, then calls `etl/scoring.py:normalize_gpa/quality/difficulty()` to produce normalized factors, then `compute_gaucho_score()` with default weights.
- **D-02:** The `gaucho_scores` table is left as-is (no new columns, no Alembic migration for Phase 2). The pre-computed scores in the table are used only by the ETL pipeline — the API computes independently.
- **D-03:** The rankings endpoint returns **default-weight score + all four raw factors** (`gpa_factor`, `quality_factor`, `difficulty_factor`, `sentiment_factor`). The endpoint does NOT accept weight query parameters. Phase 3 weight sliders recompute entirely client-side using the raw factors — no server round-trip on weight change.

### N+1 Rewrite (Phase 2 Plan 1)
- **D-04:** Phase 2 starts with a dedicated plan to rewrite `compute_all_scores()` in `etl/scoring.py`. Rewrite as a single bulk JOIN that loads all `rmp_ratings` + `avg_sentiment` + `avg_gpa` data in one query, then computes all scores in Python without per-professor DB queries. This closes FDN-03 properly. After the rewrite is confirmed working, the API plans proceed.

### FastAPI App Layout
- **D-05:** Create an `api/` package at project root with this structure:
  ```
  api/
    __init__.py
    main.py          ← app = FastAPI(); app.include_router(...)
    dependencies.py  ← get_db() generator that yields a SQLAlchemy session
    routers/
      __init__.py
      health.py      ← GET /health
      courses.py     ← GET /courses/search, GET /courses/{id}/professors
      professors.py  ← GET /professors/{id}/grades, GET /professors/{id}/comments
  ```
- **D-06:** `api/dependencies.py:get_db()` uses `db/connection.py:get_session_local()` — the session factory already configured with pool_size=5, max_overflow=10. No duplicate engine initialization.

### Test Database Strategy
- **D-07:** Use a **GitHub Actions PostgreSQL service container** (`postgres:15`) for CI. No external credentials needed. Real PostgreSQL catches dialect-specific bugs (stddev, ilike, nullslast, JSON columns) that SQLite would miss.
- **D-08:** Endpoint tests use `app.dependency_overrides[get_db]` to inject the test `db_session` fixture (the existing SAVEPOINT pattern from `tests/conftest.py`). Pattern:
  ```python
  @pytest.fixture
  def client(db_session):
      def override_get_db():
          yield db_session
      app.dependency_overrides[get_db] = override_get_db
      yield TestClient(app)
      app.dependency_overrides.clear()
  ```
- **D-09:** Update `.github/workflows/test.yml` to add a `services: postgres:` block so the PostgreSQL container is available during CI. The existing `conftest.py` `DATABASE_URL` default (`postgresql://gco:gco@localhost:5432/gco_test`) matches the service container credentials.

### Claude's Discretion
- Pydantic response models: define typed response schemas in `api/schemas.py` for all endpoints. Use `response_model=` on each route for automatic validation and OpenAPI docs.
- Input validation for course search: FastAPI `Query()` with `max_length=100` and a regex pattern `^[a-zA-Z0-9 \-]+$` — matches API-01 requirement.
- CORS: not configured in Phase 2 (deployment concern — Phase 4). Development uses `localhost:5173`.
- `pydantic-settings` for credentials: implement `api/config.py` using `pydantic-settings BaseSettings` to load `DATABASE_URL` and `RMP_AUTH_TOKEN` from environment — the "Phase 2 longer-term fix" mentioned in Phase 1 context.
- Error handling: return 404 for unknown course/professor IDs, 422 for validation errors (FastAPI default).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Requirements
- `.planning/REQUIREMENTS.md` §FastAPI Backend — API-01..05, TEST-03..04

### Existing Code to Reuse and Extend
- `dashboard/queries.py` — `search_courses()`, `get_professors_for_course()`, `get_grade_history()`, `get_comments_for_professor()`: these are the query functions the API routes will call directly
- `etl/scoring.py` — `normalize_gpa()`, `normalize_quality()`, `normalize_difficulty()`, `compute_gaucho_score()`, `compute_all_scores()` (to rewrite in Plan 1)
- `db/connection.py` — `get_session_local()`: the session factory for `api/dependencies.py:get_db()`
- `db/models.py` — all 6 ORM models; understand relationships before writing queries

### Test Infrastructure
- `tests/conftest.py` — SAVEPOINT `db_session` fixture: endpoint tests extend this with a `client` fixture using `dependency_overrides`
- `.github/workflows/test.yml` — existing CI workflow: add `services: postgres:` block here

### Phase 1 Summary (for N+1 rewrite context)
- `.planning/phases/01-foundation-bug-fixes/01-04-SUMMARY.md` — scoring N+1 patch context, current state of `etl/scoring.py`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `dashboard/queries.py:get_professors_for_course()` — already returns mean_gpa, rmp_quality, rmp_difficulty, avg_sentiment, keywords. The API rankings endpoint wraps this and adds factor normalization.
- `dashboard/queries.py:search_courses()` — already limits to 20, filters by code/title ilike. API-01 just wraps this with input validation.
- `dashboard/queries.py:get_grade_history()` — returns per-quarter grade distribution dict. Direct reuse in API-03.
- `dashboard/queries.py:get_comments_for_professor()` — returns comments with sentiment_score. Direct reuse in API-04.
- `etl/scoring.py:normalize_*()` functions — pure Python, stateless, fast. Call inline in the rankings endpoint.

### Established Patterns
- **Session management:** `db/connection.py:get_session_local()` returns a sessionmaker. `get_db()` should call `SessionLocal = get_session_local(); db = SessionLocal(); try: yield db; finally: db.close()`.
- **Test isolation:** SAVEPOINT pattern in `conftest.py` — new `client` fixture extends `db_session`, not the raw engine.
- **No inline mock data in tests:** fixtures go in `tests/fixtures/` (Phase 1 decision).

### Integration Points
- `api/main.py` imports routers and creates the FastAPI app — this is the entry point for `uvicorn api.main:app`
- `api/dependencies.py:get_db` is the single injection point for all endpoint DB sessions
- `tests/conftest.py` gets a new `client` fixture that overrides `get_db` — existing `db_session` fixture unchanged

</code_context>

<specifics>
## Specific Ideas

- `GET /courses/{id}/professors` response should include: `gaucho_score` (float), `gpa_factor` (float 0-1), `quality_factor` (float 0-1), `difficulty_factor` (float 0-1), `sentiment_factor` (float 0-1), `rmp_quality`, `rmp_difficulty`, `rmp_would_take_again`, `keywords` (list), `mean_gpa`, `quarters_taught`
- Health check must return `{"status": "ok"}` with no DB query — just a static response. Critical for UptimeRobot pings (API-05).
- `GET /courses/search?q=` query param should be validated: max 100 chars, alphanumeric + space + hyphen only (API-01)
- The N+1 rewrite for `compute_all_scores()` should use a single query: JOIN professors → grade_distributions (AVG gpa) → rmp_ratings (latest per professor) → rmp_comments (AVG sentiment), load all rows, compute scores in Python loop

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within Phase 2 scope.

</deferred>

---

*Phase: 02-fastapi-backend*
*Context gathered: 2026-03-31*

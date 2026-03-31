# Phase 2: FastAPI Backend - Research

**Researched:** 2026-03-31
**Domain:** FastAPI, Pydantic v2, SQLAlchemy session lifecycle, pytest TestClient, GitHub Actions CI
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Compute Gaucho Score fresh per-request — do not read from the `gaucho_scores` table. Rankings endpoint calls `get_professors_for_course()` to fetch raw data, then calls `normalize_gpa/quality/difficulty()` to produce factors, then `compute_gaucho_score()` with default weights.
- **D-02:** `gaucho_scores` table is left as-is. No new columns, no Alembic migration for Phase 2. Pre-computed scores are ETL-only; API computes independently.
- **D-03:** Rankings endpoint returns default-weight score + all four raw factors (`gpa_factor`, `quality_factor`, `difficulty_factor`, `sentiment_factor`). Endpoint does NOT accept weight query parameters. Phase 3 weight sliders recompute entirely client-side.
- **D-04:** Phase 2 starts with a dedicated plan to rewrite `compute_all_scores()` in `etl/scoring.py`. Rewrite as a single bulk JOIN that loads all `rmp_ratings` + `avg_sentiment` + `avg_gpa` data in one query, then computes all scores in Python without per-professor DB queries. This closes FDN-03 properly.
- **D-05:** Create an `api/` package at project root with structure: `api/__init__.py`, `api/main.py`, `api/dependencies.py`, `api/routers/__init__.py`, `api/routers/health.py`, `api/routers/courses.py`, `api/routers/professors.py`
- **D-06:** `api/dependencies.py:get_db()` uses `db/connection.py:get_session_local()`. No duplicate engine initialization.
- **D-07:** GitHub Actions PostgreSQL service container (`postgres:15`) for CI. No external credentials needed.
- **D-08:** Endpoint tests use `app.dependency_overrides[get_db]` to inject the test `db_session` fixture (SAVEPOINT pattern).
- **D-09:** Update `.github/workflows/test.yml` to add a `services: postgres:` block.

### Claude's Discretion

- Pydantic response models: define typed response schemas in `api/schemas.py` for all endpoints. Use `response_model=` on each route.
- Input validation for course search: FastAPI `Query()` with `max_length=100` and pattern `^[a-zA-Z0-9 \-]+$`.
- CORS: not configured in Phase 2 (deployment concern — Phase 4).
- `pydantic-settings` for credentials: implement `api/config.py` using `pydantic-settings BaseSettings` to load `DATABASE_URL` and `RMP_AUTH_TOKEN` from environment.
- Error handling: return 404 for unknown course/professor IDs, 422 for validation errors (FastAPI default).

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within Phase 2 scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| API-01 | Course search: up to 20 results, input validated (max 100 chars, alphanumeric + space + hyphen only) | `search_courses()` already exists; wrap with FastAPI `Query(max_length=100, pattern=...)` |
| API-02 | Professor ranking: Gaucho Score + raw factors + RMP metrics + keyword tags | `get_professors_for_course()` returns raw data; inline normalize_* calls produce factors |
| API-03 | Per-quarter grade distribution for professor+course combo | `get_grade_history()` returns complete grade dict; direct reuse in route handler |
| API-04 | Most recent RMP comments with VADER sentiment (default limit 5) | `get_comments_for_professor()` already handles ordering and limit parameter |
| API-05 | `GET /health` returns `{"status": "ok"}` with no DB query | Static response only — no Depends(get_db) on this route |
| TEST-03 | All endpoint tests pass using test db session via `dependency_overrides` | SAVEPOINT `db_session` fixture + new `client` fixture pattern confirmed |
| TEST-04 | CI runs full test suite on every push without real external calls | Existing `.github/workflows/test.yml` already has postgres:16 service; D-09 is already done |
</phase_requirements>

---

## Summary

Phase 2 builds five FastAPI REST endpoints on top of the existing `dashboard/queries.py` query functions and `etl/scoring.py` normalization functions. The implementation requires creating an `api/` package from scratch (no existing `api/` directory) and wiring it to the existing `db/connection.py` session factory.

The most important pre-work is rewriting `compute_all_scores()` in `etl/scoring.py` from a 3-queries-per-professor N+1 loop into a single bulk JOIN (D-04). This is Plan 1, and the API plans must not start until it is complete. The existing scoring N+1 causes ~35,250 queries on 11,750 pairs, which reliably drops Neon connections.

The CI infrastructure is already largely in place. The `.github/workflows/test.yml` already has a `postgres:16` service container with credentials matching the test `DATABASE_URL`. No CI changes are needed for Phase 2 (D-09 is pre-satisfied). The installed FastAPI stack (fastapi 0.128.0, pydantic 2.12.5, uvicorn 0.40.0) is functional, though fastapi 0.135.2 is the current latest — pinning to `>=0.128` in requirements is sufficient; upgrading is optional.

**Primary recommendation:** Plan 1 = N+1 bulk JOIN rewrite. Plans 2-5 = one plan per router group (health + structure, courses, professors, schemas/config). Plan 6 = endpoint tests using the `client` fixture pattern with `dependency_overrides`.

---

## Standard Stack

### Core
| Library | Version (installed) | Latest | Purpose | Why Standard |
|---------|---------------------|--------|---------|--------------|
| fastapi | 0.128.0 | 0.135.2 | HTTP framework, routing, validation, OpenAPI | Industry standard for Python APIs; Pydantic-native |
| pydantic | 2.12.5 | 2.12.5 | Response model validation and serialization | FastAPI's native schema layer; v2 is current |
| uvicorn | 0.40.0 | 0.42.0 | ASGI server | Standard FastAPI deployment server |
| sqlalchemy | >=2.0 (pinned in requirements.txt) | — | ORM session management | Already the project ORM |
| psycopg2-binary | >=2.9 (pinned) | — | PostgreSQL driver | Already in requirements.txt |

### Supporting
| Library | Version (installed) | Latest | Purpose | When to Use |
|---------|---------------------|--------|---------|-------------|
| pydantic-settings | 2.12.0 | 2.13.1 | `BaseSettings` — load config from env vars | `api/config.py` for `DATABASE_URL`, `RMP_AUTH_TOKEN` |
| httpx | 0.28.1 | 0.28.1 | HTTP client used by FastAPI TestClient | Already installed; required for `TestClient` to work |
| pytest | >=8.3 (in requirements-dev.txt) | — | Test runner | Already in requirements-dev.txt |

### Verification Notes
- `fastapi 0.128.0` is installed; `0.135.2` is latest as of 2026-03-31. The gap is minor — no breaking changes between these versions in the 0.128–0.135 range. Pinning `>=0.128,<1` is safe.
- `pydantic 2.12.5` is both installed and the current latest. Pydantic v2 is fully confirmed.
- `pydantic-settings` is a separate package from `pydantic` since v2. It is already installed (2.12.0) but NOT in `requirements.txt` — must be added.
- `httpx` is already installed but NOT in `requirements.txt` or `requirements-dev.txt`. `fastapi.testclient.TestClient` requires it. Must be added to `requirements-dev.txt`.
- `uvicorn` is already installed but NOT in `requirements.txt`. Must be added for `uvicorn api.main:app` to work without a manual install.

### Missing from requirements files (must add)
```
requirements.txt:    fastapi>=0.128,<1   uvicorn>=0.40,<1   pydantic-settings>=2.12,<3
requirements-dev.txt: httpx>=0.28,<1
```

**Installation (new packages only):**
```bash
pip install "fastapi>=0.128,<1" "uvicorn>=0.40,<1" "pydantic-settings>=2.12,<3" "httpx>=0.28,<1"
```

---

## Architecture Patterns

### Recommended Project Structure (per D-05)
```
api/
├── __init__.py
├── main.py           # app = FastAPI(); app.include_router(...)
├── config.py         # pydantic-settings BaseSettings for DATABASE_URL, RMP_AUTH_TOKEN
├── dependencies.py   # get_db() generator — yields SQLAlchemy session
├── schemas.py        # All Pydantic response models
└── routers/
    ├── __init__.py
    ├── health.py     # GET /health
    ├── courses.py    # GET /courses/search, GET /courses/{id}/professors
    └── professors.py # GET /professors/{id}/grades, GET /professors/{id}/comments
```

All in project root alongside `db/`, `etl/`, `dashboard/`, `tests/`.

### Pattern 1: get_db() Session Dependency (D-06)

The session factory `get_session_local()` is already thread-safe (double-checked locking). `get_db()` wraps it with a try/finally guarantee.

```python
# api/dependencies.py
from db.connection import get_session_local

def get_db():
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

This is a generator function. FastAPI calls it via `Depends(get_db)`, executes up to `yield`, injects the session, then runs the `finally` block after the response is sent. One session per request — no session sharing across requests.

### Pattern 2: APIRouter Structure (D-05)

```python
# api/routers/courses.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.dependencies import get_db

router = APIRouter()

@router.get("/courses/search", response_model=list[CourseResult])
def search_courses_endpoint(
    q: Annotated[str, Query(max_length=100, pattern=r"^[a-zA-Z0-9 \-]+$")],
    db: Session = Depends(get_db),
):
    ...
```

```python
# api/main.py
from fastapi import FastAPI
from api.routers import health, courses, professors

app = FastAPI(title="Gaucho Course Optimizer API")
app.include_router(health.router)
app.include_router(courses.router, prefix="/courses", tags=["courses"])
app.include_router(professors.router, prefix="/professors", tags=["professors"])
```

Note: `GET /courses/search` and `GET /courses/{id}/professors` are both in `courses.py`. Because FastAPI matches routes in order, `search` (literal path segment) must be declared BEFORE `{id}` (path parameter) — otherwise `/courses/search?q=physics` will be treated as `course_id="search"`.

### Pattern 3: Input Validation with Query() (API-01)

```python
# Source: FastAPI official docs — https://fastapi.tiangolo.com/tutorial/query-params-str-validations/
from typing import Annotated
from fastapi import Query

@router.get("/courses/search")
def search(
    q: Annotated[str, Query(max_length=100, pattern=r"^[a-zA-Z0-9 \-]+$")],
    db: Session = Depends(get_db),
):
    ...
```

FastAPI returns HTTP 422 automatically when `q` fails validation. The `Annotated` style (not `q: str = Query(...)`) is the current recommended approach in FastAPI docs.

### Pattern 4: Pydantic v2 Response Schemas (api/schemas.py)

```python
# api/schemas.py
from pydantic import BaseModel, ConfigDict

class CourseResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    title: str | None = None
    department: str | None = None

class ProfessorRanking(BaseModel):
    id: int
    name: str
    department: str | None = None
    gaucho_score: float
    gpa_factor: float
    quality_factor: float
    difficulty_factor: float
    sentiment_factor: float
    rmp_quality: float | None = None
    rmp_difficulty: float | None = None
    rmp_would_take_again: float | None = None
    rmp_num_ratings: int | None = None
    mean_gpa: float | None = None
    quarters_taught: int
    keywords: list[str] = []

class GradeQuarter(BaseModel):
    quarter: str
    avg_gpa: float | None = None
    a_plus: int
    a: int
    a_minus: int
    b_plus: int
    b: int
    b_minus: int
    c_plus: int
    c: int
    c_minus: int
    d_plus: int
    d: int
    d_minus: int
    f: int

class CommentResult(BaseModel):
    text: str | None = None
    sentiment_score: float | None = None
    keywords: list[str] | None = None
    created_at: str | None = None

class HealthResponse(BaseModel):
    status: str
```

`from_attributes=True` is the Pydantic v2 replacement for v1's `orm_mode = True`. Since the query functions return plain `dict` objects (not ORM instances), `from_attributes=True` is not strictly required — but including it is harmless and future-proofs the schemas.

### Pattern 5: Endpoint Test Client with SAVEPOINT Override (D-08)

This is the most critical pattern for TEST-03. The `db_session` fixture already exists in `tests/conftest.py`. The `client` fixture is NEW and must be added to `tests/conftest.py` (or a new `tests/test_api/conftest.py`).

```python
# tests/conftest.py — add this fixture
import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import get_db

@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
```

The `override_get_db` yields the already-open `db_session` (which is bound to the SAVEPOINT transaction). FastAPI's dependency system calls `override_get_db()`, gets the same session, and after the request completes executes the generator's teardown — but since `db_session` is already managed by the outer fixture, the `finally: db.close()` in the real `get_db()` is never called. The SAVEPOINT fixture retains control and rolls back after the test. This is the canonical pattern verified by oddbird.net and FastAPI docs.

**Important:** The `client` fixture depends on `db_session`, not `engine` directly. This ensures the test session is the one being injected — not a new session.

### Pattern 6: pydantic-settings Config (Claude's Discretion)

```python
# api/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    database_url: str = "postgresql://gco:gco@localhost:5432/gco"
    rmp_auth_token: str = ""

settings = Settings()
```

`db/connection.py` already reads `DATABASE_URL` directly via `os.environ.get("DATABASE_URL", ...)`. The `api/config.py` approach does not replace this — it adds a typed config layer that the API package can use for its own startup checks. The connection module remains as-is per D-06.

### Pattern 7: N+1 Bulk JOIN Rewrite Structure (D-04)

The existing `compute_all_scores()` does 3 DB queries per professor (RMP rating lookup + sentiment AVG + score upsert). With 11,750 pairs that is ~35,250 queries.

The rewrite loads everything in one query, then computes in Python:

```python
# etl/scoring.py — restructured compute_all_scores()
# Single query joining professors → grade_distributions (avg GPA) →
# rmp_ratings (latest per professor via subquery) →
# rmp_comments (avg sentiment via subquery)

from sqlalchemy import func
from db.models import Professor, GradeDistribution, RmpRating, RmpComment, GauchoScore

def compute_all_scores(session, weights=None):
    if weights is None:
        weights = {"gpa": 0.25, "quality": 0.25, "difficulty": 0.25, "sentiment": 0.25}

    # Subquery: latest RMP rating per professor
    latest_rating_sq = (
        session.query(
            RmpRating.professor_id,
            func.max(RmpRating.id).label("latest_rating_id"),
        )
        .group_by(RmpRating.professor_id)
        .subquery("latest_rating")
    )

    # Subquery: avg sentiment per rating
    sentiment_sq = (
        session.query(
            RmpComment.rmp_rating_id,
            func.avg(RmpComment.sentiment_score).label("avg_sentiment"),
        )
        .filter(RmpComment.sentiment_score.isnot(None))
        .group_by(RmpComment.rmp_rating_id)
        .subquery("sentiment")
    )

    # Main bulk JOIN: all data in one query
    rows = (
        session.query(
            Professor.id.label("professor_id"),
            GradeDistribution.course_id,
            func.avg(GradeDistribution.avg_gpa).label("mean_gpa"),
            RmpRating.overall_quality,
            RmpRating.difficulty,
            RmpRating.num_ratings,
            sentiment_sq.c.avg_sentiment,
        )
        .join(GradeDistribution, GradeDistribution.professor_id == Professor.id)
        .join(latest_rating_sq, latest_rating_sq.c.professor_id == Professor.id)
        .join(RmpRating, RmpRating.id == latest_rating_sq.c.latest_rating_id)
        .outerjoin(sentiment_sq, sentiment_sq.c.rmp_rating_id == RmpRating.id)
        .filter(Professor.rmp_id.isnot(None))
        .group_by(
            Professor.id,
            GradeDistribution.course_id,
            RmpRating.overall_quality,
            RmpRating.difficulty,
            RmpRating.num_ratings,
            sentiment_sq.c.avg_sentiment,
        )
        .all()
    )
    # ... compute scores in Python loop, bulk upsert
```

Note the difference from the existing `get_professors_for_course()`: that function uses `outerjoin` for RMP (professors without RMP still appear). `compute_all_scores()` uses `join` (inner) for RMP because scoring requires RMP data — professors without it are skipped (matching current behavior's `skipped` counter).

### Anti-Patterns to Avoid

- **Route order bug:** Declare `GET /courses/search` before `GET /courses/{id}/professors` in the same router. FastAPI evaluates routes in declaration order — if `{id}` comes first, the string `"search"` is treated as a course ID.
- **Session not closed:** Use `try/finally` in `get_db()`, not just `yield db`. An unhandled exception in the route handler skips code after `yield` — the `finally` block guarantees cleanup.
- **Double engine initialization:** Do not call `create_engine()` inside `api/dependencies.py`. Always use `get_session_local()` from `db/connection.py` — the engine is already configured with `pool_size=5`, `max_overflow=10`, `pool_recycle=1800`, `pool_pre_ping=True`.
- **Sharing the `client` fixture state:** `app.dependency_overrides` is a module-level dict on the `app` object. Always call `app.dependency_overrides.clear()` in the `client` fixture teardown (after `yield`) to prevent test pollution.
- **Pydantic v1 patterns in v2:** Do not use `class Config: orm_mode = True`. Use `model_config = ConfigDict(from_attributes=True)`. Do not use `validator` decorator — use `field_validator` or `model_validator`.
- **Health endpoint with DB dependency:** `GET /health` must NOT use `Depends(get_db)`. It must return a static response. Any DB dependency would make the health check fail during DB downtime — the entire point of a health endpoint is to signal server availability independently of database.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Input validation | Custom regex check in route body | `Query(max_length=100, pattern=...)` | FastAPI returns 422 with structured error; OpenAPI docs auto-generated |
| Response serialization | `jsonify(dict(...))` | `response_model=ProfessorRanking` on route | Pydantic validates output, strips extra fields, generates OpenAPI schema |
| Config from environment | `os.environ.get("DATABASE_URL")` in api/ | `pydantic-settings BaseSettings` | Type validation at startup; `.env` file support; structured error if var missing |
| Test database isolation | Truncating tables between tests | SAVEPOINT rollback (existing `db_session` fixture) | Zero cleanup code; tests cannot pollute each other; 10x faster than truncate |
| Session lifecycle | Manual `db = Session(); db.close()` inline | `get_db()` generator with `Depends` | FastAPI handles teardown on exception; single injection point for test override |

**Key insight:** FastAPI's `Query()` validation, `response_model=`, and `Depends()` are not optional niceties — they are the mechanism that generates the OpenAPI documentation and ensures the contract the React frontend depends on is enforced at the HTTP layer, not buried in application logic.

---

## Runtime State Inventory

This phase is greenfield API development, not a rename/refactor/migration. No runtime state inventory required.

---

## Common Pitfalls

### Pitfall 1: Route Order — `search` Shadowed by `{id}`
**What goes wrong:** `GET /courses/search?q=physics` matches `GET /courses/{id}/professors` with `id="search"`, returning a 404 or 422 instead of search results.
**Why it happens:** FastAPI evaluates routes in the order they are declared. Path parameters match any string.
**How to avoid:** In `api/routers/courses.py`, declare the `/search` endpoint before the `/{id}/professors` endpoint. They share the same router, so declaration order is deterministic.
**Warning signs:** Search endpoint tests pass but return 422 with `"value is not a valid integer"` error.

### Pitfall 2: `app.dependency_overrides` Leaking Between Tests
**What goes wrong:** One test sets `dependency_overrides[get_db]` but the fixture teardown fails silently, polluting subsequent tests with the wrong session.
**Why it happens:** If the `client` fixture does not call `app.dependency_overrides.clear()` in a `finally` block (or after `yield`), any exception in the test body skips the cleanup.
**How to avoid:** Use `yield TestClient(app)` pattern — the teardown after `yield` always runs. Call `app.dependency_overrides.clear()` there unconditionally.
**Warning signs:** Tests pass individually but fail when run together; test order affects results.

### Pitfall 3: Scoring Factors for Professors with No RMP Data
**What goes wrong:** `get_professors_for_course()` returns professors with `rmp_quality=None`. When the rankings endpoint calls `normalize_quality(None)`, it raises `TypeError`.
**Why it happens:** `normalize_quality()` is not None-safe — it calls `quality / 5.0` directly.
**How to avoid:** In the route handler, guard each factor: `qual_f = normalize_quality(prof["rmp_quality"]) if prof["rmp_quality"] is not None else 0.5`. Match the `compute_all_scores()` fallback of 0.5 for missing data.
**Warning signs:** Test with a professor who has no RMP rating raises 500 Internal Server Error.

### Pitfall 4: Sentiment Factor Normalization Scale Mismatch
**What goes wrong:** `avg_sentiment` from `get_professors_for_course()` is a VADER score in `[-1, 1]`. If passed directly to `compute_gaucho_score()` as the sentiment factor, it will be negative for neutral/negative professors, producing incorrect scores.
**Why it happens:** The existing `compute_all_scores()` normalizes: `sent_f = (float(avg_sentiment) + 1) / 2`. This maps `[-1, 1]` to `[0, 1]`. The same transform must be applied in the API route handler.
**How to avoid:** `sent_f = (prof["avg_sentiment"] + 1) / 2 if prof["avg_sentiment"] is not None else 0.5`.
**Warning signs:** Professors with neutral comments (avg_sentiment ≈ 0) get a sentiment_factor of 0.0 instead of 0.5, making their Gaucho Score lower than expected.

### Pitfall 5: Bulk JOIN GROUP BY in N+1 Rewrite — Missing Aggregate Columns
**What goes wrong:** PostgreSQL raises `ERROR: column "rmp_ratings.overall_quality" must appear in the GROUP BY clause or be used in an aggregate function`.
**Why it happens:** SQLAlchemy's `.group_by()` must include all non-aggregated columns in SELECT when using PostgreSQL (unlike SQLite which is lenient). The bulk JOIN query selects multiple RmpRating columns that must all be in GROUP BY.
**How to avoid:** Include `RmpRating.overall_quality`, `RmpRating.difficulty`, `RmpRating.num_ratings`, and `sentiment_sq.c.avg_sentiment` in `.group_by()`. Alternatively, use the subquery approach that pre-aggregates within subqueries before the main join.
**Warning signs:** Query works in development with SQLite but fails immediately against PostgreSQL in CI.

### Pitfall 6: `pydantic-settings` Not in requirements.txt
**What goes wrong:** `ImportError: No module named 'pydantic_settings'` on a clean install (CI, new developer, Render deployment).
**Why it happens:** `pydantic-settings` is a separate package from `pydantic` since Pydantic v2. It is installed in the local venv (confirmed: 2.12.0) but is absent from `requirements.txt`.
**How to avoid:** Add `pydantic-settings>=2.12,<3` to `requirements.txt`.
**Warning signs:** `pip install -r requirements.txt && python -c "from pydantic_settings import BaseSettings"` raises ImportError.

---

## Code Examples

Verified patterns from official sources and codebase audit:

### Health Endpoint (No DB — API-05)
```python
# api/routers/health.py
from fastapi import APIRouter
from api.schemas import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def health_check():
    return {"status": "ok"}
```

### Course Search with Validation (API-01)
```python
# api/routers/courses.py
from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from api.dependencies import get_db
from api.schemas import CourseResult
from dashboard.queries import search_courses

router = APIRouter()

@router.get("/search", response_model=list[CourseResult])
def search(
    q: Annotated[str, Query(max_length=100, pattern=r"^[a-zA-Z0-9 \-]+$")],
    db: Session = Depends(get_db),
):
    return search_courses(db, q)
```

Note: prefix `/courses` is set in `main.py` via `include_router(courses.router, prefix="/courses")`.

### Professor Rankings with Factor Computation (API-02)
```python
# api/routers/courses.py (continued)
from fastapi import HTTPException
from api.schemas import ProfessorRanking
from dashboard.queries import get_professors_for_course
from etl.scoring import normalize_gpa, normalize_quality, normalize_difficulty, compute_gaucho_score

@router.get("/{course_id}/professors", response_model=list[ProfessorRanking])
def get_professors(course_id: int, db: Session = Depends(get_db)):
    profs = get_professors_for_course(db, course_id)
    if not profs:
        raise HTTPException(status_code=404, detail="Course not found or no professors")
    results = []
    for p in profs:
        gpa_f = normalize_gpa(p["mean_gpa"]) if p["mean_gpa"] is not None else 0.5
        qual_f = normalize_quality(p["rmp_quality"]) if p["rmp_quality"] is not None else 0.5
        diff_f = normalize_difficulty(p["rmp_difficulty"]) if p["rmp_difficulty"] is not None else 0.5
        # VADER [-1,1] → sentiment factor [0,1]
        sent_f = (p["avg_sentiment"] + 1) / 2 if p["avg_sentiment"] is not None else 0.5
        score = compute_gaucho_score(gpa_f, qual_f, diff_f, sent_f)
        results.append({**p, "gaucho_score": score, "gpa_factor": gpa_f,
                        "quality_factor": qual_f, "difficulty_factor": diff_f,
                        "sentiment_factor": sent_f})
    return sorted(results, key=lambda x: x["gaucho_score"], reverse=True)
```

### Test Client Fixture (TEST-03)
```python
# tests/conftest.py — add to existing file
import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import get_db

@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
```

### Endpoint Test Pattern
```python
# tests/test_api_health.py
def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

# tests/test_api_courses.py
def test_search_validates_special_chars(client):
    response = client.get("/courses/search?q=CS@%23!")
    assert response.status_code == 422

def test_search_returns_results(client, db_session):
    from db.models import Course
    db_session.add(Course(code="CMPSC8", title="Intro", department="CMPSC"))
    db_session.flush()
    response = client.get("/courses/search?q=CMPSC")
    assert response.status_code == 200
    assert len(response.json()) >= 1
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Pydantic v1 `class Config: orm_mode = True` | `model_config = ConfigDict(from_attributes=True)` | Pydantic v2 (2023) | Old syntax raises `PydanticUserError` in v2 |
| Pydantic v1 `@validator` | `@field_validator` / `@model_validator` | Pydantic v2 (2023) | Old decorator not available in v2 |
| `q: str = Query(default=None, ...)` | `q: Annotated[str, Query(...)] = None` | FastAPI 0.95+ | `Annotated` style is recommended; old style still works |
| `Optional[str]` import | `str \| None` union syntax | Python 3.10+ / PEP 604 | Cleaner; project requires Python 3.12 so union syntax is safe |
| N+1 per-professor scoring loop | Single bulk JOIN + Python loop | Phase 2 Plan 1 | Reduces 35,250 queries to ~3 queries per `compute_all_scores()` run |

**Deprecated/outdated:**
- `pydantic.BaseSettings`: Moved to separate `pydantic-settings` package in Pydantic v2. Importing from `pydantic` directly raises ImportError.
- `RmpRating.fetched_at` ordering in `get_session_local` fix: The bulk JOIN rewrite uses `func.max(RmpRating.id)` as the "latest rating" selector (same as `get_professors_for_course()`), not `fetched_at`. This is intentional — sequential ETL inserts make `max(id)` equivalent to most recent.

---

## Open Questions

1. **`get_grade_history` course_id parameter source**
   - What we know: `GET /professors/{id}/grades` (API-03) requires both `professor_id` and `course_id`. The `get_grade_history(session, professor_id, course_id)` function signature requires both. But the route is `GET /professors/{id}/grades` — there's no `course_id` in the path.
   - What's unclear: Should `course_id` be a required query parameter (`?course_id=42`), an optional filter, or should the endpoint return all courses for the professor if omitted?
   - Recommendation: Add `course_id: int` as a required query parameter to keep the API consistent with the function signature. Use `Query(gt=0)` for validation. The frontend will always know the course_id (user selected it). This is a discretionary implementation choice — flag for the planner to confirm.

2. **`search_courses()` title search vs. code-only**
   - What we know: `search_courses()` only filters on `Course.code.ilike(f"%{query}%")` — it does not search `Course.title`. API-01 says "search for courses by name or code".
   - What's unclear: Should Phase 2 extend the query to also search `Course.title`? Or is the existing code-only search sufficient for the v1.0 launch?
   - Recommendation: Extend to OR filter on title as well (`Course.code.ilike(...) | Course.title.ilike(...)`). This is a minor query change and matches the stated requirement. But it modifies an existing tested function — the planner should decide whether this is Plan 2 work or a separate task.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 | All API code | ✓ | 3.12.0 | — |
| fastapi | API framework | ✓ | 0.128.0 | — |
| pydantic | Response models | ✓ | 2.12.5 | — |
| pydantic-settings | api/config.py | ✓ | 2.12.0 | Use os.environ directly (weaker) |
| uvicorn | Run server locally | ✓ | 0.40.0 | — |
| httpx | TestClient backend | ✓ | 0.28.1 | — |
| pytest | Test runner | ✓ | in requirements-dev.txt | — |
| PostgreSQL (local) | Test suite locally | ✗ | — | Use docker-compose.yml (already in repo) |
| PostgreSQL (CI) | TEST-04 | ✓ | postgres:16 in .github/workflows/test.yml | Already configured |

**Missing dependencies with no fallback:**
- None that block execution. All packages installed in venv.

**Missing dependencies with fallback:**
- Local PostgreSQL for test runs: Not available natively on this machine. The `docker-compose.yml` in the repo provides a `postgres:15` container with matching credentials. Developers run `docker-compose up -d` before `pytest`.
- Package registry gaps (pydantic-settings, uvicorn, httpx not in requirements files): These are installed but will be missing on CI or new developer machines unless added to requirements files.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3+ |
| Config file | `pyproject.toml` — `[tool.pytest.ini_options]` (testpaths=["tests"], pythonpath=["."]) |
| Quick run command | `pytest tests/test_api_health.py tests/test_api_courses.py tests/test_api_professors.py -x` |
| Full suite command | `pytest -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| API-01 | Search validates max_length=100, alphanumeric+space+hyphen | unit | `pytest tests/test_api_courses.py::test_search_validates_special_chars -x` | ❌ Wave 0 |
| API-01 | Search returns up to 20 results | unit | `pytest tests/test_api_courses.py::test_search_returns_results -x` | ❌ Wave 0 |
| API-02 | Rankings returns gaucho_score + 4 raw factors | unit | `pytest tests/test_api_courses.py::test_get_professors_returns_factors -x` | ❌ Wave 0 |
| API-02 | Rankings returns 404 for unknown course_id | unit | `pytest tests/test_api_courses.py::test_get_professors_unknown_course -x` | ❌ Wave 0 |
| API-03 | Grade history returns per-quarter data | unit | `pytest tests/test_api_professors.py::test_get_grades -x` | ❌ Wave 0 |
| API-04 | Comments returns 5 most recent with sentiment | unit | `pytest tests/test_api_professors.py::test_get_comments -x` | ❌ Wave 0 |
| API-05 | Health returns `{"status": "ok"}` with no DB call | unit | `pytest tests/test_api_health.py::test_health -x` | ❌ Wave 0 |
| TEST-03 | All endpoint tests use db_session fixture via overrides | integration | `pytest tests/test_api_*.py -v` | ❌ Wave 0 |
| TEST-04 | CI runs full suite on push | smoke | `pytest -v` (in CI) | ✓ (workflow exists, no changes needed) |
| FDN-03 | compute_all_scores() executes single bulk JOIN | unit | `pytest tests/test_scoring.py::test_compute_all_scores_bulk -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_api_health.py -x` (smoke)
- **Per wave merge:** `pytest -v` (full suite)
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_api_health.py` — covers API-05
- [ ] `tests/test_api_courses.py` — covers API-01, API-02
- [ ] `tests/test_api_professors.py` — covers API-03, API-04
- [ ] `tests/conftest.py` — add `client` fixture (file exists, needs `client` fixture appended)
- [ ] `tests/test_scoring.py` — add `test_compute_all_scores_bulk` for FDN-03 (file exists, needs new test)
- [ ] Framework install: none required (pytest already in requirements-dev.txt)

---

## Sources

### Primary (HIGH confidence)
- FastAPI official docs — https://fastapi.tiangolo.com/tutorial/sql-databases/ — session dependency pattern
- FastAPI official docs — https://fastapi.tiangolo.com/tutorial/bigger-applications/ — APIRouter structure
- FastAPI official docs — https://fastapi.tiangolo.com/tutorial/query-params-str-validations/ — Query() validation
- FastAPI official docs — https://fastapi.tiangolo.com/tutorial/testing/ — TestClient + dependency_overrides
- Pydantic v2 docs — https://docs.pydantic.dev/latest/concepts/models/ — BaseModel, ConfigDict, from_attributes
- Pydantic Settings docs — https://docs.pydantic.dev/latest/concepts/pydantic_settings/ — BaseSettings pattern
- GitHub Actions docs — https://docs.github.com/en/actions/use-cases-and-examples/using-containerized-services/creating-postgresql-service-containers — service container configuration
- PyPI version check (pip index versions) — verified: fastapi 0.135.2 latest, pydantic 2.12.5 latest, uvicorn 0.42.0 latest, pydantic-settings 2.13.1 latest
- Installed package audit (pip show) — confirmed installed versions: fastapi 0.128.0, pydantic 2.12.5, pydantic-settings 2.12.0, uvicorn 0.40.0, httpx 0.28.1

### Secondary (MEDIUM confidence)
- OddBird article (2024-02-09) — https://www.oddbird.net/2024/02/09/testing-fastapi/ — SAVEPOINT + dependency_overrides interaction; verified against FastAPI TestClient docs

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — packages are installed and verified against PyPI; versions confirmed
- Architecture: HIGH — patterns verified against FastAPI official docs; codebase audit confirms no `api/` package exists yet
- Pitfalls: HIGH for route order, session cleanup, factor normalization (derived from codebase reading); MEDIUM for GROUP BY pitfall (derived from PostgreSQL behavior knowledge)
- N+1 rewrite: HIGH — existing code structure read directly; rewrite pattern mirrors existing `get_professors_for_course()` subquery approach

**Research date:** 2026-03-31
**Valid until:** 2026-04-30 (FastAPI releases frequently; core patterns stable)

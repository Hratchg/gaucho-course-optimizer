# Architecture Research

**Domain:** React + FastAPI presentation layer on top of existing Python ETL pipeline
**Researched:** 2026-03-30
**Confidence:** HIGH (based on direct inspection of existing source + verified stack research)

---

## Context

This document answers the integration question for v1.0: how does the new FastAPI + React layer connect to the existing Python 3.12 / SQLAlchemy / PostgreSQL / APScheduler codebase? It identifies new files to create, existing files to modify, the exact integration seams, and the build order that respects dependencies.

**Guiding constraint:** The ETL pipeline (`scrapers/`, `etl/`, `scheduler/`, `db/`) is NOT touched. Only the presentation layer is replaced: `dashboard/` is deprecated and a new `api/` module + `frontend/` directory are added.

---

## System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│  BROWSER (Vercel CDN)                                                │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  React SPA  (frontend/)                                        │  │
│  │  Vite + TypeScript + TanStack Query + Recharts + shadcn/ui    │  │
│  │                                                                │  │
│  │  Pages:  /  (search)   /course/:id  (professor list)          │  │
│  └────────────────────────┬───────────────────────────────────────┘  │
└───────────────────────────│──────────────────────────────────────────┘
                            │  HTTPS REST (axios, VITE_API_URL)
                            │
┌───────────────────────────▼──────────────────────────────────────────┐
│  RENDER FREE TIER                                                    │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  FastAPI  (api/)                                               │  │
│  │  uvicorn, pydantic-settings, CORS middleware                  │  │
│  │                                                                │  │
│  │  GET /health                                                   │  │
│  │  GET /courses/search?q=...                                     │  │
│  │  GET /courses/{id}/professors                                  │  │
│  │  GET /professors/{id}/comments                                 │  │
│  │  GET /professors/{id}/grades?course_id=...                     │  │
│  └──────────┬─────────────────────────────────────────────────────┘  │
│             │  import (same Python process)                          │
│  ┌──────────▼──────────────────────────────────────────────────────┐ │
│  │  EXISTING: db/ (SQLAlchemy, models.py, connection.py)          │ │
│  │  EXISTING: etl/ (scoring.py — compute_gaucho_score() reused)   │ │
│  │  EXISTING: dashboard/queries.py  ← query logic migrated here  │ │
│  └──────────┬──────────────────────────────────────────────────────┘ │
│             │  SQL (psycopg2, pool_pre_ping=True)                    │
└─────────────│────────────────────────────────────────────────────────┘
              │
┌─────────────▼────────────────────────────────────────────────────────┐
│  NEON SERVERLESS POSTGRESQL                                          │
│  (same schema — professors, courses, grade_distributions,           │
│   rmp_ratings, rmp_comments, gaucho_scores)                         │
└──────────────────────────────────────────────────────────────────────┘

Separately (runs on its own cron / CLI invocation):
┌─────────────────────────────────────────────────────────────────────┐
│  EXISTING ETL PIPELINE (unchanged)                                  │
│  scheduler/jobs.py + scripts/run_pipeline.py                        │
│  scrapers/ → etl/ → db/ → Neon                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Responsibilities

| Component | Status | Responsibility |
|-----------|--------|----------------|
| `api/main.py` | NEW | FastAPI app factory, lifespan, CORS middleware, router registration |
| `api/config.py` | NEW | pydantic-settings `Settings` class — DATABASE_URL, RMP_AUTH_TOKEN, FRONTEND_URL |
| `api/dependencies.py` | NEW | `get_db()` generator that wraps `db/connection.py` as a FastAPI `Depends()` |
| `api/routers/courses.py` | NEW | `GET /courses/search`, `GET /courses/{id}/professors` |
| `api/routers/professors.py` | NEW | `GET /professors/{id}/comments`, `GET /professors/{id}/grades` |
| `api/routers/health.py` | NEW | `GET /health` — no DB call, used by UptimeRobot keepalive |
| `api/schemas/course.py` | NEW | Pydantic response models: `CourseResult`, `ProfessorSummary` |
| `api/schemas/professor.py` | NEW | Pydantic response models: `CommentOut`, `GradeRecord`, `ProfessorFactors` |
| `frontend/` | NEW | React SPA (Vite + TypeScript) — all UI |
| `db/connection.py` | MODIFIED (minor) | Add `SessionLocal = sessionmaker(...)` export so `api/dependencies.py` can import it cleanly. No logic change. |
| `db/models.py` | DO NOT TOUCH | Schema is fixed for v1.0. No new columns. |
| `dashboard/queries.py` | SOURCE ONLY | Query logic is extracted from here into `api/routers/`. The file itself is not deleted (Streamlit still works locally) but no new code goes here. |
| `dashboard/app.py` | DEPRECATED | Not deleted in v1.0 — kept for local reference. Not deployed. |
| `etl/scoring.py` | REUSED | `compute_gaucho_score()` is imported directly by `api/routers/courses.py` for in-request re-ranking with custom weights. No changes. |
| `scheduler/jobs.py` | DO NOT TOUCH | APScheduler handles all data refresh. No changes. |
| `scrapers/` | DO NOT TOUCH | All scraping stays as-is. |
| `requirements.txt` | MODIFIED | Add: `fastapi`, `uvicorn`, `pydantic-settings`, `python-multipart` |
| `render.yaml` | NEW | Render IaC config (optional but recommended) |
| `vercel.json` | NEW | SPA rewrite rule for React Router deep links |

---

## New Directory Structure

Only the additions / changes. The existing tree is unchanged.

```
gaucho-course-optimizer/
├── api/                         # NEW — FastAPI application
│   ├── __init__.py
│   ├── main.py                  # App factory, CORS, router includes
│   ├── config.py                # pydantic-settings Settings
│   ├── dependencies.py          # get_db() Depends wrapper
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── health.py            # GET /health
│   │   ├── courses.py           # GET /courses/search, GET /courses/{id}/professors
│   │   └── professors.py        # GET /professors/{id}/comments, /grades
│   └── schemas/
│       ├── __init__.py
│       ├── course.py            # CourseResult, ProfessorSummary, ProfessorFactors
│       └── professor.py         # CommentOut, GradeRecord
│
├── frontend/                    # NEW — React SPA
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── package.json
│   ├── src/
│   │   ├── main.tsx             # React root, QueryClientProvider, RouterProvider
│   │   ├── api.ts               # axios instance (baseURL from VITE_API_URL)
│   │   ├── pages/
│   │   │   ├── SearchPage.tsx   # / — course search autocomplete
│   │   │   └── CoursePage.tsx   # /course/:id — professor ranking list
│   │   ├── components/
│   │   │   ├── ProfessorCard.tsx
│   │   │   ├── GradeChart.tsx   # Recharts BarChart
│   │   │   ├── GpaTrendChart.tsx # Recharts LineChart
│   │   │   ├── WeightSliders.tsx
│   │   │   ├── CommentList.tsx
│   │   │   └── ui/              # shadcn/ui copies (Command, Card, Badge, Skeleton)
│   │   ├── hooks/
│   │   │   ├── useCourseSearch.ts    # TanStack Query wrapper
│   │   │   └── useProfessors.ts      # TanStack Query wrapper
│   │   └── types/
│   │       └── api.ts           # TypeScript interfaces matching Pydantic schemas
│   └── public/
│
├── vercel.json                  # NEW — SPA rewrite rule
├── render.yaml                  # NEW (optional) — Render IaC
├── requirements.txt             # MODIFIED — add FastAPI deps
└── .env.example                 # MODIFIED — add FRONTEND_URL, note Neon DATABASE_URL format
```

---

## Integration Points

### 1. FastAPI → db/connection.py (critical seam)

The existing `db/connection.py` exposes `get_session()` which creates a new `Session` per call. FastAPI needs a `Depends()`-compatible generator. The fix is minimal: add one export alias to `connection.py`, then wrap it in `api/dependencies.py`.

**What to add in `db/connection.py`** (the only change to this file):
```python
# Add after existing code — do not change existing get_engine() or get_session()
SessionLocal = sessionmaker(bind=get_engine())
```

**`api/dependencies.py`** (new file):
```python
from db.connection import SessionLocal
from typing import Generator
from sqlalchemy.orm import Session

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

This approach preserves the existing sync SQLAlchemy session without touching engine configuration. The `pool_pre_ping=True` already set in `get_engine()` handles Neon's scale-to-zero reconnects automatically.

### 2. FastAPI → dashboard/queries.py (query migration)

The four query functions in `dashboard/queries.py` are the direct source for API router logic:

| Existing function | Maps to API endpoint | Notes |
|------------------|---------------------|-------|
| `search_courses(session, query, department)` | `GET /courses/search?q=&dept=` | Copy logic; keep `.ilike` pattern, keep 20-result limit |
| `get_professors_for_course(session, course_id, min_year)` | `GET /courses/{id}/professors` | N+1 bug here (RMP + sentiment queried per-professor in a loop) — fix in API router using a single JOIN |
| `get_grade_history(session, professor_id, course_id)` | `GET /professors/{id}/grades?course_id=` | Copy as-is; simple ordered query |
| `get_comments_for_professor(session, professor_id, limit)` | `GET /professors/{id}/comments?limit=` | Copy as-is; already ordered by `created_at.desc()` |

The N+1 in `get_professors_for_course` is the critical one to fix: it runs 2 additional queries per professor (RMP rating + sentiment aggregate). Rewrite as a single query joining `GradeDistribution + Professor + RmpRating + RmpComment` with aggregates.

### 3. FastAPI → etl/scoring.py (weight slider re-ranking)

The weight sliders on the React frontend require re-ranking without a server round-trip. The correct architecture is:

1. API response for `GET /courses/{id}/professors` includes **raw normalized factor values** for each professor (not just the stored score).
2. React applies `compute_gaucho_score` equivalent in the browser when slider weights change.

The API must return these fields in `ProfessorSummary`:
```
gpa_factor: float        # normalize_gpa(mean_gpa)  — 0.0–1.0
quality_factor: float    # bayesian-adjusted normalize_quality(rmp_quality) — 0.0–1.0
difficulty_factor: float # normalize_difficulty(rmp_difficulty) — 0.0–1.0
sentiment_factor: float  # (avg_sentiment + 1) / 2  — 0.0–1.0
gaucho_score: float      # pre-computed with default weights (for initial render)
```

The `etl/scoring.py` normalization functions (`normalize_gpa`, `normalize_quality`, `normalize_difficulty`, `bayesian_adjust`) are imported directly in the API router to compute these values on the fly — the stored `GauchoScore` table holds batch-computed scores, but the API computes fresh factors at request time for slider compatibility.

**React-side score formula** (TypeScript, in `CoursePage.tsx` or a utility):
```typescript
function computeGauchoScore(
  factors: { gpa: number; quality: number; difficulty: number; sentiment: number },
  weights: { gpa: number; quality: number; difficulty: number; sentiment: number }
): number {
  const raw =
    factors.gpa * weights.gpa +
    factors.quality * weights.quality +
    factors.difficulty * weights.difficulty +
    factors.sentiment * weights.sentiment;
  return Math.round(Math.max(0, Math.min(100, raw * 100)) * 10) / 10;
}
```

This eliminates a round-trip on every slider drag. Weights sum to 1.0 — the React UI must enforce this (e.g., normalize automatically or lock the fourth slider).

### 4. React → FastAPI (CORS + env)

The only runtime coupling between the two deployed services is the `VITE_API_URL` environment variable (set in Vercel dashboard) and the CORS `allow_origins` list in `api/main.py` (set to the production Vercel URL). Both must be configured before the first deployment — if CORS is misconfigured, the browser silently drops all API responses.

See STACK.md for the exact CORS configuration pattern. The critical point: `allow_origins=["*"]` in production is wrong; list the exact Vercel domain.

### 5. Existing db/models.py (do not touch)

The schema is complete for v1.0. The API reads from:
- `professors` — name, department, match_confidence, rmp_id
- `courses` — code, title, department
- `grade_distributions` — per-quarter grade counts and avg_gpa
- `rmp_ratings` — overall_quality, difficulty, would_take_again_pct, num_ratings
- `rmp_comments` — comment_text, sentiment_score, keywords, created_at
- `gaucho_scores` — stored score for initial default-weight render (optimization)

No migration needed for v1.0.

---

## API Contract (Endpoint Specifications)

These are the five endpoints the React app requires. Pydantic schemas must match exactly so the TypeScript types in `frontend/src/types/api.ts` can be generated or manually mirrored.

### GET /health
```json
{ "status": "ok" }
```
No DB call. Used by UptimeRobot keepalive ping (every 5 min to avoid Render cold starts).

### GET /courses/search?q={query}&dept={department}
```json
[
  { "id": 1, "code": "CMPSC 111", "title": "Introduction to Computational Science", "department": "Computer Science" }
]
```
- Max 20 results, ordered by `code`
- `q` is required, `dept` is optional filter
- Use `.ilike(f"%{query}%")` as in existing `search_courses()` — this is the search UX entry point

### GET /courses/{course_id}/professors
```json
[
  {
    "id": 42,
    "name": "Richert Wang",
    "department": "Computer Science",
    "mean_gpa": 3.41,
    "std_gpa": 0.18,
    "quarters_taught": 6,
    "rmp_quality": 4.2,
    "rmp_difficulty": 3.1,
    "rmp_would_take_again": 87.5,
    "rmp_num_ratings": 34,
    "avg_sentiment": 0.38,
    "keywords": ["fair exams", "helpful", "clear lectures"],
    "match_confidence": 0.92,
    "gaucho_score": 72.4,
    "gpa_factor": 0.853,
    "quality_factor": 0.798,
    "difficulty_factor": 0.58,
    "sentiment_factor": 0.69
  }
]
```
- Ordered by `gaucho_score` descending
- Includes raw factors for client-side weight slider re-ranking
- Fix N+1: batch-load all RMP ratings and sentiment aggregates in one query before the loop

### GET /professors/{professor_id}/grades?course_id={course_id}
```json
[
  {
    "quarter": "Fall 2023",
    "avg_gpa": 3.2,
    "a_plus": 5, "a": 18, "a_minus": 7,
    "b_plus": 4, "b": 9, "b_minus": 3,
    "c_plus": 2, "c": 1, "c_minus": 0,
    "d_plus": 0, "d": 0, "d_minus": 0,
    "f": 1
  }
]
```
Ordered by year asc, quarter asc. Maps directly from `get_grade_history()` in `dashboard/queries.py`.

### GET /professors/{professor_id}/comments?limit={n}
```json
[
  {
    "text": "Really helpful office hours, exams are fair.",
    "sentiment_score": 0.72,
    "keywords": ["office hours", "fair exams"],
    "created_at": "Mar 2024"
  }
]
```
Default `limit=5`. Maps directly from `get_comments_for_professor()`.

---

## Data Flow: Course Search to Ranked List

```
User types "CS 16" in search box
    ↓ (debounced 300ms)
useCourseSearch hook fires GET /courses/search?q=CS+16
    ↓
FastAPI courses.py router
    → get_db() injects SQLAlchemy session
    → search_courses() logic: Course.code.ilike("%CS 16%") LIMIT 20
    → Returns list[CourseResult]
    ↓
React renders autocomplete dropdown (shadcn/ui Command)

User selects "CMPSC 16"
    ↓
React Router navigates to /course/1
    ↓
useProfessors hook fires GET /courses/1/professors
    ↓
FastAPI courses.py router
    → get_professors_for_course() with N+1 fix
    → compute_gaucho_score() for each prof using default weights
    → Returns list[ProfessorSummary] with factors + score, ordered by score DESC
    ↓
React renders professor cards with Gaucho Score badge (default weights)

User drags GPA weight slider
    ↓
computeGauchoScore() called in browser with new weights
    → No API call
    → Professor list re-sorted in React state
    ↓
Cards re-render with updated scores
```

---

## Build Order

The build order below is based on hard dependencies: you cannot test an API endpoint without the DB layer, you cannot build the frontend without an API contract, and you cannot deploy without both.

### Phase 1 — Foundation (no new features, fix what's broken)

**Goal:** Pipeline runs clean end-to-end on Neon. All existing bugs fixed. Test suite covers pipeline.

**Files touched:**
- `db/connection.py` — add `SessionLocal` export (the only structural prep for Phase 2)
- `requirements.txt` — add Neon SSL connection string support (already handled by psycopg2)
- `.env.example` — update DATABASE_URL comment to Neon format
- `tests/` — add pipeline tests, fix N+1 in `dashboard/queries.py` (the N+1 fix is done here, not in the API — the API routers will reuse the fixed query pattern)

**Do NOT create `api/` yet.** Fixing bugs first means the API layer is built on a verified data foundation.

**Rationale:** Building FastAPI on top of N+1 queries means the API will be slow in production and hard to debug. Fix the data layer before the presentation layer.

### Phase 2 — FastAPI Backend

**Goal:** Five endpoints working and returning correct data. Can be tested with curl/Swagger UI.

**Build sequence within this phase:**

1. `api/config.py` — Settings class first (everything else needs DATABASE_URL)
2. `api/dependencies.py` — get_db() generator (routers need this)
3. `api/routers/health.py` — `/health` endpoint (smoke test the server boots)
4. `api/schemas/course.py` + `api/schemas/professor.py` — define response contracts before writing logic
5. `api/routers/courses.py` — `/courses/search` (simplest, no joins), then `/courses/{id}/professors` (complex, uses scoring.py)
6. `api/routers/professors.py` — `/professors/{id}/grades` and `/professors/{id}/comments`
7. `api/main.py` — wire everything together, CORS config
8. `tests/test_api_courses.py`, `tests/test_api_professors.py` — endpoint tests using the existing `conftest.py` DB fixture

**Rationale:** Schemas before logic prevents back-and-forth between routers and Pydantic models. Health endpoint first confirms the server boots before adding DB-dependent routes.

### Phase 3 — React Frontend

**Goal:** SPA renders correct data from the Phase 2 API. No placeholder data.

**Build sequence within this phase:**

1. `frontend/` scaffold — `npm create vite@latest frontend -- --template react-ts`
2. `frontend/src/api.ts` — axios instance with `VITE_API_URL` baseURL (wire to local FastAPI first)
3. `frontend/src/types/api.ts` — TypeScript interfaces mirroring Phase 2 Pydantic schemas
4. `frontend/src/pages/SearchPage.tsx` — course search + autocomplete (depends on `/courses/search`)
5. `frontend/src/hooks/useCourseSearch.ts` — TanStack Query wrapper for search
6. `frontend/src/pages/CoursePage.tsx` — professor list, skeleton loading states (depends on `/courses/{id}/professors`)
7. `frontend/src/hooks/useProfessors.ts` — TanStack Query wrapper
8. `frontend/src/components/ProfessorCard.tsx` — Gaucho Score badge, RMP data, keywords
9. `frontend/src/components/WeightSliders.tsx` + in-browser `computeGauchoScore()` (depends on factors in API response)
10. `frontend/src/components/GradeChart.tsx` — Recharts BarChart (depends on `/professors/{id}/grades`)
11. `frontend/src/components/GpaTrendChart.tsx` — Recharts LineChart over same data
12. `frontend/src/components/CommentList.tsx` — sentiment-tagged comments (depends on `/professors/{id}/comments`)
13. `vercel.json` — SPA rewrite rule (add before any routing tests)

**Rationale:** Search page before course page (it's the entry point). Data-display components before interactive ones (weight sliders need the cards to exist first). `vercel.json` added early to avoid confusion when testing React Router.

### Phase 4 — Deployment

**Goal:** Both services live, CORS working, cold start mitigated.

**Build sequence:**

1. Provision Neon database, load `data/gco_dump.sql` (or re-run pipeline)
2. Deploy FastAPI to Render — set `DATABASE_URL` (Neon), `RMP_AUTH_TOKEN`, `FRONTEND_URL` env vars
3. Verify `/health` returns 200 on Render URL
4. Set `VITE_API_URL` in Vercel dashboard to Render service URL
5. Deploy React to Vercel — verify autocomplete works end-to-end
6. Configure UptimeRobot: free monitor pinging `https://[render-url]/health` every 5 minutes
7. Update CORS `allow_origins` in `api/main.py` to include the final Vercel production URL (not preview URL)

---

## Components That Must NOT Be Changed

The following existing files are load-bearing for the ETL pipeline and must not be modified during v1.0 frontend work:

| File | Why frozen |
|------|-----------|
| `db/models.py` | Schema changes require Alembic migration + data migration + ETL retesting. No schema changes in v1.0. |
| `etl/enhanced_matcher.py` | 4-pass matching engine. Changes here require re-running matching on entire professor table. |
| `etl/nlp_processor.py` | VADER + TF-IDF pipeline. Changes require re-processing all comments. |
| `etl/scoring.py` | Gaucho Score formula. Changes invalidate all stored `gaucho_scores`. Import functions; do not modify them. |
| `scheduler/jobs.py` | APScheduler cron configuration. Changes affect data freshness. |
| `scrapers/rmp_scraper.py` | RMP GraphQL client with rate limiting. Changes risk API ban. |
| `scrapers/targeted_scrape.py` | Main scrape orchestrator. Leave as-is. |

The `dashboard/` directory can be left in place for local development reference but is not deployed or extended.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Recreating the Session Factory

**What people do:** Write a new `engine = create_engine(...)` in `api/main.py` or `api/dependencies.py`, duplicating what `db/connection.py` already does.

**Why it's wrong:** Creates two engine instances, two connection pools, and potential divergence between `DATABASE_URL` sources. The ETL pipeline and scheduler already use `get_engine()` — the API must use the same singleton.

**Do this instead:** Import `SessionLocal` from `db/connection.py`. One engine, one pool, shared by all consumers.

### Anti-Pattern 2: Running compute_all_scores() on Every Request

**What people do:** Call `etl/scoring.py:compute_all_scores()` when the `/courses/{id}/professors` endpoint is hit to ensure scores are fresh.

**Why it's wrong:** `compute_all_scores()` iterates all (professor, course) pairs and writes to DB. It's a batch operation taking seconds, not a request handler. It will timeout on Render free tier.

**Do this instead:** Compute factors on the fly for just the professors in the response using the normalization functions. The batch `gaucho_scores` table is used only for default-weight pre-computation. Real-time re-ranking happens in the browser.

### Anti-Pattern 3: Storing Slider Weights Server-Side

**What people do:** POST the user's slider weights to the API, have the server recompute and return a sorted list.

**Why it's wrong:** Creates a round-trip on every slider drag (300ms+ on Render free tier after cold start). The normalized factors are already in the API response — the browser has everything it needs.

**Do this instead:** Return `gpa_factor`, `quality_factor`, `difficulty_factor`, `sentiment_factor` in the professor list response. Apply `computeGauchoScore()` in the browser.

### Anti-Pattern 4: Migrating to Async SQLAlchemy for FastAPI

**What people do:** See FastAPI async docs, decide to migrate to `asyncpg` + `async_sessionmaker` to "do it right."

**Why it's wrong:** The existing codebase uses sync SQLAlchemy throughout. Async migration requires rewriting every query in `dashboard/queries.py`, changing `get_engine()`, updating the ETL pipeline, and re-testing everything. The benefit (non-blocking I/O) is irrelevant on a free-tier server with 0.1 CPU and essentially no concurrent traffic.

**Do this instead:** Keep sync SQLAlchemy. Use `Depends(get_db)` with a sync generator. FastAPI handles sync endpoints correctly. If a specific endpoint becomes a bottleneck, wrap it with `run_in_executor` at that point.

### Anti-Pattern 5: Wildcard CORS in Production

**What people do:** Set `allow_origins=["*"]` because it's easier and "it's just a student project."

**Why it's wrong:** Allows any origin to make requests to the API. For a read-only public API this is low risk, but it prevents future auth headers from working (CORS credentials require explicit origins) and is visible in public code.

**Do this instead:** List the exact Vercel production URL. Add `localhost:5173` for dev. The STACK.md has the exact configuration.

---

## Scaling Considerations

This is a student tool for UCSB's ~26,000 undergrads. Registration peak is 2–3 weeks per quarter (three times per year). The Render + Vercel + Neon free tier architecture is appropriate for this scale.

| Scale | Approach |
|-------|----------|
| 0–500 users/day | Current architecture — Render free tier, single uvicorn worker, Neon free tier |
| 500–5,000 users/day | Upgrade Render to Starter ($7/mo) for always-on (no cold starts), add DB indexes on `courses.code` and `grade_distributions(professor_id, course_id)` |
| 5,000+ users/day | Add Redis response caching (`GET /courses/{id}/professors` is read-heavy, data changes only when pipeline runs); move Neon to paid tier for dedicated compute |

For v1.0, the only scaling action worth taking is adding missing DB indexes (already flagged as a bug in PROJECT.md). Everything else is premature.

---

## Sources

- Direct inspection of `db/connection.py`, `db/models.py`, `dashboard/queries.py`, `etl/scoring.py` — HIGH confidence
- `.planning/research/STACK.md` — FastAPI structure, CORS config, Render deployment — HIGH confidence
- `.planning/codebase/ARCHITECTURE.md` — existing pipeline architecture — HIGH confidence
- FastAPI dependency injection docs: https://fastapi.tiangolo.com/tutorial/dependencies/
- FastAPI SQL databases guide: https://fastapi.tiangolo.com/tutorial/sql-databases/
- TanStack Query background refetch: https://tanstack.com/query/latest/docs/framework/react/guides/background-fetching-indicators

---

*Architecture research for: React + FastAPI presentation layer on Python ETL*
*Researched: 2026-03-30*

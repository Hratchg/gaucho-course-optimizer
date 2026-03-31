# Project Research Summary

**Project:** Gaucho Course Optimizer — Web Frontend + API Layer
**Domain:** React SPA + FastAPI REST layer over existing Python ETL pipeline (UCSB professor ranking tool)
**Researched:** 2026-03-30
**Confidence:** HIGH

---

## Executive Summary

The Gaucho Course Optimizer v1.0 milestone adds a public-facing React SPA and FastAPI REST layer on top of a working Python 3.12 / SQLAlchemy / PostgreSQL ETL pipeline. The core strategic insight from research is that **this is a thin presentation layer, not a new application**: the data is already there, the scoring engine already works, and the Streamlit prototype already validates what students want. The job is to expose it cleanly without touching the ETL infrastructure. Every architectural decision flows from this constraint: wrap, don't rewrite.

The recommended stack is FastAPI 0.115.x + uvicorn (single worker on Render free tier) for the API, with Pydantic v2 response schemas and a minimal wrapper over the existing sync SQLAlchemy sessions. The React frontend uses Vite 8 + TypeScript + TanStack Query v5 + Recharts + shadcn/ui + Tailwind v4, deployed to Vercel. The single most critical infrastructure decision is to use **Neon for PostgreSQL hosting** — Render's free-tier database now expires every 30 days, which would destroy all scraped data on a predictable schedule.

The top risks are operational, not architectural: CORS misconfiguration between the two deployed services is the most common silent production failure; Render's 15-minute cold start will frustrate first visitors without an explicit UptimeRobot keepalive; and the existing codebase has three pre-existing bugs (missing DB indexes, no connection pool limits, N+1 query in `dashboard/queries.py`) that must be fixed before the API layer is built on top of them. None of these are blockers — they are known, documented, and fixable in a dedicated bug-fix phase before the API work begins.

---

## Key Findings

### Recommended Stack

The backend adds only four Python packages to `requirements.txt`: `fastapi`, `uvicorn`, `pydantic-settings`, and `python-multipart`. Everything else — SQLAlchemy, psycopg2, APScheduler, VADER, the scoring engine — is already present and stays unchanged. The API module is a new `api/` directory that imports from `db/` and `etl/` as a consumer, never as a modifier.

The React frontend is a new `frontend/` directory scaffolded with `npm create vite@latest frontend -- --template react-ts`. Key packages: `@tanstack/react-query@^5` for server state (replaces manual `useEffect` fetch patterns), `axios` with a single `api.ts` instance configured from `VITE_API_URL`, `recharts` for grade distribution charts (lightest viable option at ~230 KB), and `react-router-dom` v6 for `/course/:id` routing. shadcn/ui components are copied into the repo — no bundle overhead for unused components.

**Core technologies:**
- **FastAPI 0.115.x:** REST API framework — native async, automatic OpenAPI docs, first-class Pydantic v2 integration, matches Python 3.12 runtime
- **uvicorn (single worker):** ASGI server — Render free tier has 0.1 CPU; multi-worker Gunicorn causes OOM kills, not throughput gains
- **pydantic-settings 2.x:** Environment config — type-safe `BaseSettings` replaces scattered `os.environ.get()` calls
- **Neon serverless PostgreSQL:** DB hosting — never-expiring free tier; Render's free DB deletes itself every 30 days since May 2024
- **React 19 + Vite 8 + TypeScript 5.7:** Frontend — concurrent features (useTransition) benefit search UX; Rolldown-based Vite 8 is 10-30x faster builds
- **TanStack Query v5:** Server state — correct tool for a read-heavy SPA; handles caching, stale-while-revalidate, loading/error states
- **Recharts 2.x:** Charts — SVG, pure React components, ~230 KB, sufficient for BarChart grade distributions
- **shadcn/ui:** Components — Command (autocomplete), Card, Badge, Skeleton; zero bundle bloat for unused parts

**What to avoid:** Next.js (adds Node server, not needed for this SPA), async SQLAlchemy migration (high rewrite risk, zero benefit at this traffic level), Redux/Zustand for server state (TanStack Query handles it), Gunicorn multi-worker on free tier (OOM risk), Render PostgreSQL as primary DB (30-day expiry).

### Expected Features

No existing tool at UCSB fuses grade distributions + RMP data + NLP sentiment into a single ranked, customizable score. The competitive moat is the Gaucho Score with real-time weight sliders — no competitor offers customizable ranking formulas. Everything else is table stakes that students already expect from UCSBPlat and RMP.

**Must have (table stakes) — ship in v1.0:**
- Course search with autocomplete — absence causes immediate friction; fires on 1-2 characters, keyboard-navigable
- Professor ranking list per course ordered by Gaucho Score — the core promise of the tool
- Gaucho Score displayed per professor with visual indicator — single number for at-a-glance comparison
- Grade distribution bar chart (% per letter grade, per professor per course) — every UCSB competitor shows this
- GPA trend line chart over quarters — students want trajectory, not just a snapshot
- RMP quality / difficulty / "would take again" display — saves the RMP tab switch
- Recent RMP comments with VADER sentiment badge — students read comments more than scores
- Mobile-responsive layout — GOLD is used on phones during 7 AM registration pass times
- Loading states and skeleton loaders — Render cold starts require explicit "waking up" feedback

**Should have (differentiators) — include in v1.0:**
- Real-time weight sliders (Gaucho Score formula) — the primary differentiator; validated in Streamlit prototype; scores recompute in browser without an API round-trip
- Keyword tags on professor card (TF-IDF extracted) — surfaces signal faster than reading 30 comments; already in pipeline output

**Defer to v1.1:**
- Quarter-by-quarter grade filter dropdown — useful but adds API complexity; all-time data is sufficient for launch
- Professor side-by-side comparison view — valuable but scope risk; ranked list answers the core question

**Defer indefinitely (anti-features):**
- User accounts / saved favorites — adds auth, liability, negligible benefit for 2-3 uses per quarter
- Review submission — requires moderation; RMP already collects reviews
- AI chatbot — GauchoClass already exists; adds LLM cost and hallucination risk
- Schedule builder — UCSBPlat already does this; separate product scope
- Department/school-level rankings — different product, dilutes value proposition

### Architecture Approach

The system is two deployed services with a single integration point: the React SPA on Vercel CDN calls the FastAPI service on Render via HTTPS REST, and the FastAPI service reads from Neon PostgreSQL using the existing sync SQLAlchemy engine. The ETL pipeline runs independently (APScheduler / CLI) and writes to the same Neon database. There is no shared session, no message queue, no bidirectional coupling. The FastAPI module (`api/`) imports from `db/` and `etl/` as a pure consumer — no file in those directories is modified.

The weight slider feature is the key architectural decision for the frontend: the API must return raw normalized factor values (`gpa_factor`, `quality_factor`, `difficulty_factor`, `sentiment_factor`) alongside the pre-computed `gaucho_score`. React applies `computeGauchoScore()` in the browser on slider drag — no round-trip. This requires the `etl/scoring.py` normalization functions to be called per-professor at request time in the API router (not the batch `compute_all_scores()` function).

**Major components:**

1. `api/` (NEW) — FastAPI app: `config.py` (pydantic-settings), `dependencies.py` (get_db wrapper), `routers/` (courses, professors, health), `schemas/` (Pydantic response models). Wraps `db/` and `etl/scoring.py` without modifying them.
2. `frontend/` (NEW) — React SPA: `pages/` (SearchPage, CoursePage), `components/` (ProfessorCard, GradeChart, GpaTrendChart, WeightSliders, CommentList, shadcn/ui copies), `hooks/` (useCourseSearch, useProfessors via TanStack Query), `types/api.ts` (TypeScript interfaces mirroring Pydantic schemas).
3. `db/connection.py` (MINOR MODIFICATION) — Add one `SessionLocal = sessionmaker(bind=get_engine())` export so `api/dependencies.py` can import it. No other changes to `db/`.
4. `etl/scoring.py` (REUSED, NOT MODIFIED) — `compute_gaucho_score()` and normalization functions imported by API routers for per-request factor computation. The batch `compute_all_scores()` function is never called from the API.
5. `dashboard/queries.py` (SOURCE REFERENCE ONLY) — Query logic is migrated into `api/routers/` with the N+1 bug fixed. The file is not deleted but receives no new code.
6. Neon PostgreSQL — External DB; `pool_pre_ping=True` handles scale-to-zero reconnects; `sslmode=require` in connection string.
7. `vercel.json` (NEW) — SPA rewrite rule (`"source": "/(.*)", "destination": "/index.html"`) required for React Router deep links.

**Five API endpoints (complete contract):**
- `GET /health` — no DB call; used by UptimeRobot keepalive
- `GET /courses/search?q=&dept=` — max 20 results, ilike search with input validation
- `GET /courses/{course_id}/professors` — ranked list with raw factors + score; N+1 fixed via single JOIN
- `GET /professors/{id}/grades?course_id=` — per-quarter grade records for charts
- `GET /professors/{id}/comments?limit=` — sentiment-tagged comments, default limit 5

### Critical Pitfalls

1. **Render PostgreSQL 30-day expiry** — Use Neon as the PostgreSQL host (free tier, no expiry). Never provision a Render-native free database as the primary store. Decision must be made before first deploy.

2. **CORS misconfiguration** — Set `allow_origins` to the exact Vercel production URL plus `http://localhost:5173` (never `["*"]`). Read CORS origins from a `FRONTEND_URL` env var to avoid code changes for Vercel preview URLs. Place `CORSMiddleware` as the first middleware. Verify before React integration — browser drops all responses silently on CORS failure.

3. **N+1 query in `dashboard/queries.py`** — The `get_professors_for_course()` function runs 2 additional queries per professor (RMP rating + sentiment). With 10 professors, that is 21 queries. Fix with a single JOIN query in the API router before writing any frontend code. Builds on a broken query = slow production API.

4. **Missing DB indexes** — No indexes on `professor_id`/`course_id` foreign keys in `db/models.py`. Sequential scans on `grade_distributions` will degrade as data grows. Add indexes in a migration or `__table_args__` before first production deploy.

5. **SQLAlchemy connection pool exhaustion** — No pool limits configured in `db/connection.py`. FastAPI's sync threadpool (40 threads default) can exhaust Render's PostgreSQL connection limit (~25). Fix: `pool_size=5, max_overflow=10, pool_recycle=1800, pool_pre_ping=True` before the API is built.

6. **Vite bakes `VITE_API_URL` at build time** — If `.env` contains `http://localhost:8000` and Vercel builds without the dashboard env var set, the production bundle silently calls localhost. Set `VITE_API_URL` in Vercel's dashboard, not in any committed file.

7. **Render cold start (15-min inactivity sleep)** — First request after dormancy takes 30-60 seconds. Add a `/health` endpoint and configure a free UptimeRobot ping every 10 minutes. Show "Waking up the server..." in the React UI after 3 seconds of waiting.

---

## Implications for Roadmap

Based on the dependency chain from research, a 4-phase structure is required. The phases are sequentially dependent: Phase 1 fixes the data layer, Phase 2 exposes it via API, Phase 3 renders it in React, Phase 4 deploys it. Skipping or parallelizing phases causes building on broken foundations.

### Phase 1: Foundation and Bug Fixes

**Rationale:** Three pre-existing bugs (missing indexes, no connection pool limits, N+1 query) will make the production API slow or unresponsive. These must be fixed before the API is built on top of them — debugging performance in a FastAPI layer is harder than fixing it directly in `db/` and `dashboard/queries.py`. The ETL pipeline must also be verified running clean against Neon.

**Delivers:** A verified, performant data layer. Neon is provisioned and connected. The pipeline runs end-to-end. Existing tests pass. No more critical infrastructure warnings in CONCERNS.md.

**Addresses:** Pre-conditions for all subsequent features (everything in FEATURES.md depends on clean data).

**Avoids:**
- Connection pool exhaustion under any concurrent load (Pitfall 3)
- N+1 query degrading the professor ranking endpoint (Pitfall 2 + 11)
- Missing indexes causing silent query degradation (Pitfall 11)
- Render PostgreSQL 30-day data loss (Pitfall 4)
- Hardcoded RMP auth token in source code (Pitfall 12)

**Files touched:** `db/connection.py` (add pool config + `SessionLocal` export), `db/models.py` (add indexes via `__table_args__`), `dashboard/queries.py` (fix N+1), `scrapers/rmp_scraper.py` (remove hardcoded token), `.env.example` (Neon DATABASE_URL format), `requirements.txt` (add FastAPI deps), `tests/` (add pipeline tests, mock HTTP for scraper tests).

### Phase 2: FastAPI Backend

**Rationale:** The API contract must be defined and verified before any React code is written. TypeScript interfaces in the frontend must mirror Pydantic schemas exactly — defining both simultaneously causes drift. The health endpoint is built first as a smoke test, schemas are defined before routers (not after), and CORS is configured and verified with curl before any browser code touches it.

**Delivers:** Five working endpoints verified via Swagger UI / curl. Correct data shapes for React consumption. CORS validated from localhost.

**Implements:** `api/` directory (config, dependencies, routers, schemas), `render.yaml` (optional IaC), endpoint tests using `app.dependency_overrides` to inject the SAVEPOINT fixture session.

**Uses:** FastAPI 0.115.x, uvicorn, pydantic-settings, `etl/scoring.py` normalization functions for per-request factor computation.

**Avoids:**
- Recreating the session factory (use `SessionLocal` from `db/connection.py` — Pitfall: duplicate engine)
- Running `compute_all_scores()` per request (use per-request normalization functions only — Architecture anti-pattern 2)
- APScheduler jobs sharing request sessions (each job creates its own `SessionLocal()` context — Pitfall 1)
- Wildcard CORS in production (exact origin list — Pitfall 6)
- TestClient bypassing SAVEPOINT fixture (dependency_overrides pattern — Pitfall 8)

**Build sequence within phase:** `config.py` → `dependencies.py` → `health.py` → schemas → `courses.py` router → `professors.py` router → `main.py` (wire + CORS) → endpoint tests.

### Phase 3: React Frontend

**Rationale:** React is built last because it has zero value without a working API. The entry point (SearchPage) is built before the detail page (CoursePage). Data-display components are built before interactive ones (WeightSliders require ProfessorCard to exist). `vercel.json` is added early to avoid React Router 404s during development. TypeScript interfaces in `types/api.ts` are defined first and act as the contract between frontend and backend.

**Delivers:** Full SPA: course search with autocomplete, professor ranking list with Gaucho Score, grade distribution chart, GPA trend chart, sentiment-tagged comments, real-time weight sliders. Mobile-responsive. Skeleton loading states for cold start UX.

**Addresses:** All v1.0 table stakes and differentiators from FEATURES.md (course search, ranking, grade chart, GPA trend, RMP display, comments, weight sliders, keyword tags, mobile layout, loading states).

**Avoids:**
- `VITE_API_URL` baked in as localhost (set in Vercel dashboard, not `.env` — Pitfall 7)
- Hover-only interactions that break on mobile (use click/tap for all critical info)
- Fixed-pixel chart widths that break on small screens (use Recharts `width="100%"` with `aspect` ratio)

**Build sequence within phase:** Vite scaffold → `api.ts` (axios instance) → `types/api.ts` → SearchPage → `useCourseSearch` hook → CoursePage + `useProfessors` hook → ProfessorCard → WeightSliders + `computeGauchoScore()` → GradeChart → GpaTrendChart → CommentList → `vercel.json`.

### Phase 4: Deployment

**Rationale:** Deployment is last because both services must be independently functional before cross-service CORS is verified. The sequence matters: provision the database first (data must exist before API serves it), deploy API second (Render URL must be known before Vercel build), deploy React third (sets `VITE_API_URL` to known Render URL), configure keepalive last (nothing to ping until both services are live).

**Delivers:** Both services live in production. CORS working between exact domains. Cold start mitigated via UptimeRobot. Production smoke test passing end-to-end.

**Avoids:**
- Vercel building with wrong `VITE_API_URL` (set dashboard env var before triggering production build — Pitfall 7)
- CORS blocking production requests (update `allow_origins` to final Vercel URL after deploy — Pitfall 6)
- Render env vars missing on first deploy (pre-populate all required vars before `render deploy` — Pitfall 15)
- Cold start with no user feedback (loading state + UptimeRobot `/health` ping — Pitfall 5)

**Build sequence within phase:** Provision Neon + load data → deploy FastAPI to Render (set env vars) → verify `/health` → set `VITE_API_URL` in Vercel → deploy React → configure UptimeRobot → update CORS to final Vercel URL → end-to-end smoke test.

### Phase Ordering Rationale

- Phase 1 before Phase 2: building a FastAPI layer on top of the N+1 query and no connection pool limits guarantees a slow, unreliable API. Fix the foundation first.
- Phase 2 before Phase 3: TypeScript interfaces mirror Pydantic schemas. Writing React components against a speculative API contract causes back-and-forth rewrites. Working curl tests against the real API make frontend development deterministic.
- Phase 3 before Phase 4: A deployment without a working local-to-API connection path will be very hard to debug — CORS and env var issues are nearly impossible to distinguish from application bugs without a known-good local baseline.
- Within Phase 2, schemas before routers: defining `CourseResult` and `ProfessorSummary` schemas before writing router logic prevents the common cycle of writing a router, realizing the schema is wrong, and rewriting both.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1 (Bug Fixes):** The Alembic vs. `__table_args__` decision for adding indexes needs a brief investigation of the existing migration state. CONCERNS.md mentions this but the codebase has no `alembic/` directory visible in the initial scan — if no migration history exists, `create_all` with `__table_args__` is simpler.
- **Phase 2 (FastAPI):** The exact query shape needed to fix the N+1 in `get_professors_for_course` with the existing SQLAlchemy models (joining `GradeDistribution + Professor + RmpRating + RmpComment` with aggregates) should be prototyped before writing the router. ARCHITECTURE.md describes the intent but the exact SQLAlchemy join syntax depends on the actual relationship definitions in `db/models.py`.

Phases with well-documented patterns (standard, skip research-phase):
- **Phase 3 (React):** Vite + TanStack Query + Recharts + shadcn/ui all have excellent official documentation. The component tree from ARCHITECTURE.md is complete and directly implementable.
- **Phase 4 (Deployment):** Render and Vercel deployment are fully covered in STACK.md with exact config snippets. No research needed — follow the documented pattern.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All major decisions verified against official docs and changelogs. Vite 8 confirmed released March 2026. Neon free tier terms verified. Render 30-day DB expiry verified via official changelog. |
| Features | HIGH (core), MEDIUM (competitive gaps) | Core features validated by Streamlit prototype usage. Competitive analysis based on direct tool inspection (UCSBPlat, RMP, GauchoClass). V1.1 feature value is inference-based. |
| Architecture | HIGH | Based on direct inspection of existing source files (`db/connection.py`, `db/models.py`, `dashboard/queries.py`, `etl/scoring.py`). Integration seams are concrete, not speculative. |
| Pitfalls | HIGH (critical), MEDIUM (minor) | Critical pitfalls (Render DB expiry, CORS, N+1, connection pool) are sourced from official docs and verified FastAPI/SQLAlchemy GitHub issues. Minor pitfalls are sourced from code inspection. |

**Overall confidence:** HIGH

### Gaps to Address

- **Alembic migration state:** The codebase may or may not have an initialized Alembic environment. The index-addition strategy in Phase 1 depends on this. Check for `alembic/` directory at project start; if absent, use `__table_args__` directly in `db/models.py`.
- **RMP auth token validity:** PITFALLS.md identifies a hardcoded base64 token (`dGVzdDp0ZXN0`) in `rmp_scraper.py`. Whether the actual production token is stored elsewhere or still hardcoded is unclear from static analysis alone. Verify and migrate to `pydantic-settings` in Phase 1.
- **Vercel preview URL CORS strategy:** For solo development, adding only the stable production Vercel URL to `allow_origins` is sufficient. If multiple contributors are doing PR preview reviews, the `FRONTEND_URL` env var pattern described in STACK.md should be used to add preview URLs dynamically. Decision can be deferred to Phase 4.
- **Weight slider UX enforcement:** The four weight sliders must sum to 1.0. Whether to normalize automatically (slide one, adjust others proportionally) or lock the fourth slider is a UX decision not resolved by research. Either is acceptable for v1.0 — decide during Phase 3 implementation.

---

## Sources

### Primary (HIGH confidence)
- Direct source inspection: `db/connection.py`, `db/models.py`, `dashboard/queries.py`, `etl/scoring.py`, `scheduler/jobs.py` — architecture integration seams
- FastAPI official docs: https://fastapi.tiangolo.com/ — CORS, dependencies, lifespan, SQL databases
- Render changelog (30-day DB expiry): https://render.com/changelog/free-postgresql-instances-now-expire-after-30-days-previously-90
- Neon free tier docs: https://neon.com/docs/introduction/plans
- TanStack Query v5 announcement: https://tanstack.com/blog/announcing-tanstack-query-v5
- Vite 8.0 announcement: https://vite.dev/blog/announcing-vite8
- pydantic-settings docs: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- FastAPI + SQLAlchemy deadlock issues: https://github.com/fastapi/fastapi/discussions/6628, /issues/3205

### Secondary (MEDIUM confidence)
- UCSBPlat (https://ucsbplat.com) — direct competitor feature comparison
- GauchoClass Devpost (https://devpost.com/software/gauchocourse) — competitive AI chatbot approach
- Render production best practices: https://render.com/articles/fastapi-production-deployment-best-practices
- Render cold start mitigation: https://medium.com/@saveriomazza/how-to-keep-your-fastapi-server-active-on-renders-free-tier-93767b70365c
- LogRocket React chart libraries 2025: https://blog.logrocket.com/best-react-chart-libraries-2025/

### Tertiary (LOW confidence)
- V1.1 feature value estimates (quarter filter, comparison view) — inference from Streamlit prototype usage patterns, no user study

---

*Research completed: 2026-03-30*
*Ready for roadmap: yes*

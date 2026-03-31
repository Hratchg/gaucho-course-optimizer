# Roadmap: Gaucho Course Optimizer

## Overview

v1.0 takes a working but internal Python ETL pipeline and exposes it as a public-facing web app. The work proceeds in four sequential phases: fix the data layer so the API is fast, build the API so the frontend has a contract, build the frontend so students can actually use it, then deploy so it's public. Each phase gates the next — there is no parallelism between phases because each one provides the foundation the next requires.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation & Bug Fixes** - Verify the ETL pipeline end-to-end, fix critical bugs, and establish a clean data layer on Neon PostgreSQL
- [ ] **Phase 2: FastAPI Backend** - Build and test five REST endpoints that expose course search, professor ranking, grade data, comments, and health check
- [ ] **Phase 3: React Frontend** - Build the full student-facing SPA with course search, professor cards, charts, weight sliders, and mobile-responsive layout
- [ ] **Phase 4: Deployment** - Deploy both services publicly, configure CORS, and set up cold-start mitigation

## Phase Details

### Phase 1: Foundation & Bug Fixes
**Goal**: The data layer is verified, performant, and safe to build on — pipeline runs end-to-end against Neon, critical bugs are fixed, and tests cover core scoring logic
**Depends on**: Nothing (first phase)
**Requirements**: FDN-01, FDN-02, FDN-03, FDN-04, FDN-05, FDN-06, TEST-01, TEST-02
**Success Criteria** (what must be TRUE):
  1. Developer can run the full ETL pipeline (scrape → match → NLP → score) and confirm professor-course records with Gaucho Scores are present in the Neon database
  2. Developer can run `pytest` and see pipeline tests (scraping, matching, scoring) pass with mocked HTTP — no real calls to RMP or Daily Nexus
  3. Developer can run `pytest` and see Gaucho Score formula tests pass for known inputs
  4. Application handles concurrent API requests — connection pool is configured and the database does not exhaust connections under load
  5. Professor ranking query executes as a single JOIN, and database foreign-key indexes exist so queries remain fast as data grows
**Plans:** 4 plans

Plans:
- [x] 01-01-PLAN.md — Connection pool, FK indexes, RMP auth token, VADER caching verification
- [x] 01-02-PLAN.md — N+1 query fix and Gaucho Score formula tests
- [ ] 01-03-PLAN.md — Retrofit mocking on all scraper tests for deterministic CI
- [ ] 01-04-PLAN.md — Neon DB seeding, pipeline smoke test, weekly pg_dump GitHub Action

### Phase 2: FastAPI Backend
**Goal**: Five REST endpoints are live, tested against a fixture database, and return correctly shaped data ready for React consumption — including raw factor values that enable client-side score recomputation
**Depends on**: Phase 1
**Requirements**: API-01, API-02, API-03, API-04, API-05, TEST-03, TEST-04
**Success Criteria** (what must be TRUE):
  1. Developer can call `GET /health` and receive `{"status": "ok"}` with no database query
  2. Developer can call `GET /courses/search?q=physics` and receive up to 20 validated results — input with special characters or excessive length is rejected
  3. Developer can call `GET /courses/{id}/professors` and receive a ranked list with Gaucho Score, raw factor values (`gpa_factor`, `quality_factor`, `difficulty_factor`, `sentiment_factor`), RMP metrics, and keyword tags
  4. Developer can call `GET /professors/{id}/grades` and `GET /professors/{id}/comments` and receive correctly shaped grade distribution and sentiment-tagged comment data
  5. Developer can run `pytest` and see all endpoint tests pass using the test database session fixture — CI runs the full suite on every push without real HTTP calls
**Plans**: TBD

### Phase 3: React Frontend
**Goal**: UCSB students can search for any course, see professors ranked by Gaucho Score with all supporting data visible, adjust weights to rerank instantly in the browser, and use the app on a phone
**Depends on**: Phase 2
**Requirements**: UI-01, UI-02, UI-03, UI-04, UI-05, UI-06, UI-07, UI-08, UI-09, UI-10, UI-11
**Success Criteria** (what must be TRUE):
  1. Student can type a partial course name or code and see autocomplete suggestions appear, navigable by keyboard, firing after 1-2 characters
  2. Student can select a course and see all professors ranked by Gaucho Score with color-banded score indicators, grade distribution bar charts, GPA trend line charts, RMP metrics, keyword tags, and the 5 most recent RMP comments with VADER sentiment badges
  3. Student can drag four weight sliders and see the professor list rerank instantly in the browser with no API round-trip
  4. Student can use the app on a mobile phone — professor cards stack full-width, charts resize responsively, all interactive elements have adequate touch targets
  5. Student sees skeleton loading cards while the API responds, and a "Waking up the server..." message appears after 3 seconds of waiting
**Plans**: TBD
**UI hint**: yes

### Phase 4: Deployment
**Goal**: Both services are live at public URLs, CORS is correctly scoped to the production Vercel domain, and the Render service stays warm during UCSB registration hours
**Depends on**: Phase 3
**Requirements**: DEPLOY-01, DEPLOY-02, DEPLOY-03
**Success Criteria** (what must be TRUE):
  1. Student can access the React SPA at a public Vercel URL and navigate directly to `/course/:id` deep links without a 404
  2. Student's browser can make API calls from the Vercel URL to the Render service without CORS errors — no wildcard origins in production
  3. Render API service responds within normal latency during UCSB registration hours — UptimeRobot pings `/health` every 10 minutes to prevent cold starts
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Bug Fixes | 2/4 | In progress | - |
| 2. FastAPI Backend | 0/? | Not started | - |
| 3. React Frontend | 0/? | Not started | - |
| 4. Deployment | 0/? | Not started | - |

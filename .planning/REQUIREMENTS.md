# Requirements: Milestone v1.0 Launch

**Milestone:** v1.0 Launch  
**Goal:** Replace the internal Streamlit prototype with a public-facing React + FastAPI web app so UCSB students can search courses and find the best professor.  
**Status:** Active  
**Last updated:** 2026-03-30

---

## v1.0 Requirements

### Foundation & Bug Fixes

- [ ] **FDN-01**: Developer can run the full ETL pipeline end-to-end (scrape → match → NLP → score) and verify professor-course records and Gaucho Scores are present in the database
- [ ] **FDN-02**: Application handles concurrent API requests without connection pool exhaustion (`pool_size=5`, `max_overflow=10`, `pool_recycle=1800`, `pool_pre_ping=True`)
- [ ] **FDN-03**: Professor ranking query executes a single JOIN (not N+1) — 10 professors = 1 query, not 21
- [ ] **FDN-04**: Database indexed on `professor_id` and `course_id` foreign keys so queries do not degrade as data grows
- [ ] **FDN-05**: API server starts with no hardcoded credentials — RMP auth token loaded from environment variable with no default fallback
- [ ] **FDN-06**: Application data persists indefinitely — PostgreSQL hosted on Neon free tier (not Render's 30-day-expiring free DB)

### Testing

- [ ] **TEST-01**: Developer can run `pytest` and verify ETL pipeline functions (data scraping, name matching, Gaucho Score computation) pass with mocked HTTP — no real calls to RMP or Daily Nexus
- [ ] **TEST-02**: Developer can run `pytest` and verify Gaucho Score formula produces correct output for known inputs
- [ ] **TEST-03**: Developer can run `pytest` and verify all FastAPI endpoints return correct responses using the test database session fixture (via `app.dependency_overrides`)
- [ ] **TEST-04**: CI pipeline on GitHub Actions runs the full test suite on every push without real external HTTP calls

### FastAPI Backend

- [ ] **API-01**: Student can search for courses by name or code and receive up to 20 matching results (input validated: max 100 chars, alphanumeric + space + hyphen only)
- [ ] **API-02**: Student can retrieve a ranked list of professors for a course including: Gaucho Score, raw normalized factor values (`gpa_factor`, `quality_factor`, `difficulty_factor`, `sentiment_factor`), RMP quality/difficulty/"would take again", and keyword tags
- [ ] **API-03**: Student can retrieve per-quarter grade distribution data (percentage per letter grade) for a professor-course combination
- [ ] **API-04**: Student can retrieve the most recent RMP comments for a professor with VADER sentiment scores (default limit: 5)
- [ ] **API-05**: Monitoring service can call `GET /health` and receive an immediate `{"status": "ok"}` response with no database query

### React Frontend

- [ ] **UI-01**: Student can type a partial course name or code and see matching courses appear as autocomplete suggestions (fires after 1–2 characters, keyboard-navigable via shadcn/ui Command component)
- [ ] **UI-02**: Student can select a course and see all professors ranked by Gaucho Score, with the score displayed prominently on each card (color-banded visual indicator)
- [ ] **UI-03**: Student can view a grade distribution bar chart (percentage per letter grade A+/A/A-/…/F) per professor using Recharts
- [ ] **UI-04**: Student can view a GPA trend line chart (average GPA by quarter) per professor to see trajectory over time
- [ ] **UI-05**: Student can view RMP quality score, difficulty score, and "would take again" percentage for each professor
- [ ] **UI-06**: Student can read the 5 most recent RMP comments for a professor with a VADER sentiment badge (positive/neutral/negative) on each
- [ ] **UI-07**: Student can adjust four weight sliders (GPA weight, RMP quality weight, difficulty weight, sentiment weight) and see the professor list re-ranked instantly in the browser — no API round-trip
- [ ] **UI-08**: Student can see keyword tags extracted from professor reviews on each professor card (TF-IDF keywords already computed in pipeline)
- [ ] **UI-09**: Student can use the app on a mobile phone with professor cards stacked full-width, charts sized responsively (Recharts `width="100%"`), and all interactive elements with adequate touch targets (min 44px)
- [ ] **UI-10**: Student sees skeleton loading cards (shadcn/ui Skeleton) while the API responds, including during Render cold start
- [ ] **UI-11**: Student sees a "Waking up the server…" message after 3 seconds of waiting, so they understand free-tier cold start latency

### Deployment

- [ ] **DEPLOY-01**: Student can access the React SPA at a public Vercel URL with React Router deep links working (via `vercel.json` rewrite rule)
- [ ] **DEPLOY-02**: Student's browser can make API calls to the Render service without CORS errors — `allow_origins` set to exact Vercel production URL + `http://localhost:5173`
- [ ] **DEPLOY-03**: Render API service stays warm during UCSB registration hours — UptimeRobot pings `GET /health` every 10 minutes

---

## Future Requirements (v1.1)

- Quarter-by-quarter grade filter dropdown — useful but adds API complexity; all-time data is sufficient for launch
- Professor side-by-side comparison view — valuable but scope risk; ranked list answers the core question
- Data freshness timestamp in footer — polish-level; add after core features stabilize
- Recently viewed courses (localStorage, no backend) — low value for 2–3 uses/quarter

---

## Out of Scope

| Excluded | Reason |
|----------|--------|
| User accounts / saved favorites | Adds auth complexity, liability for student data storage; negligible benefit for 2–3 uses per quarter |
| Review submission | Requires moderation, spam prevention; RMP already collects reviews — don't become a review platform |
| AI chatbot / natural language query | GauchoClass already does this; adds LLM cost and hallucination risk; ranked list is faster for the use case |
| Course schedule builder | UCSBPlat already does this; separate product scope requiring GOLD API integration |
| Department/school-level rankings | Different product with different data needs; dilutes the focused value proposition |
| Admin dashboard | Out of scope for student-facing app; pipeline management stays CLI-based |
| Notifications / email alerts | Requires email infrastructure and user data storage; incompatible with free-tier constraints |
| Professor photos | No decision-making value; privacy concerns |

---

## Traceability

| REQ-ID | Phase | Status |
|--------|-------|--------|
| FDN-01 | Phase 1 | Pending |
| FDN-02 | Phase 1 | Pending |
| FDN-03 | Phase 1 | Pending |
| FDN-04 | Phase 1 | Pending |
| FDN-05 | Phase 1 | Pending |
| FDN-06 | Phase 1 | Pending |
| TEST-01 | Phase 1 | Pending |
| TEST-02 | Phase 1 | Pending |
| API-01 | Phase 2 | Pending |
| API-02 | Phase 2 | Pending |
| API-03 | Phase 2 | Pending |
| API-04 | Phase 2 | Pending |
| API-05 | Phase 2 | Pending |
| TEST-03 | Phase 2 | Pending |
| TEST-04 | Phase 2 | Pending |
| UI-01 | Phase 3 | Pending |
| UI-02 | Phase 3 | Pending |
| UI-03 | Phase 3 | Pending |
| UI-04 | Phase 3 | Pending |
| UI-05 | Phase 3 | Pending |
| UI-06 | Phase 3 | Pending |
| UI-07 | Phase 3 | Pending |
| UI-08 | Phase 3 | Pending |
| UI-09 | Phase 3 | Pending |
| UI-10 | Phase 3 | Pending |
| UI-11 | Phase 3 | Pending |
| DEPLOY-01 | Phase 4 | Pending |
| DEPLOY-02 | Phase 4 | Pending |
| DEPLOY-03 | Phase 4 | Pending |

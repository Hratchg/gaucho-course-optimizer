# Phase 3: React Frontend - Context

**Gathered:** 2026-04-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Build a React SPA that wraps the Phase 2 FastAPI backend. Students can search UCSB courses using an autocomplete input, select a course to see all professors ranked by Gaucho Score, view grade distribution charts and RMP data, adjust four weight sliders to rerank instantly in the browser (no API round-trip), and use the entire app on a mobile phone. No new backend work. No deployment. Frontend only.

</domain>

<decisions>
## Implementation Decisions

### Professor Card Layout
- **D-01:** Compact card by default — professor name, Gaucho Score (prominent), avg GPA, RMP quality/difficulty/WTRA, and keyword tags are all visible without expanding.
- **D-02:** A single expand toggle at the bottom of each card reveals BOTH sections together: the grade distribution bar chart + GPA trend line chart (from Phase 2 API) AND the 5 most recent RMP comments with VADER sentiment badges.
- **D-03:** Gaucho Score color banding — **Claude's discretion** on visual implementation (colored left border strip, badge, or score text color). Thresholds follow Streamlit prototype: ≥70 green, 50–69 yellow, <50 red.
- **D-04:** Collapsed card header (always visible): professor name, Gaucho Score, avg GPA, RMP quality/difficulty/"would take again", keyword tags. No expansion needed to compare professors.

### Weight Sliders
- **D-05:** Desktop layout — left sidebar, always visible alongside the professor list. Sliders stay in view while scrolling through results (same paradigm as Streamlit prototype).
- **D-06:** Mobile layout — **Claude's discretion**. shadcn/ui's Sheet component (bottom drawer) is the natural fit: "Adjust weights" button above the results, tapping opens a bottom sheet with the four sliders.
- **D-07:** Numeric weight display — **Claude's discretion**. Show the current normalized weight value next to each slider label if it fits cleanly in the sidebar layout.

### URL Routing
- **D-08:** Shareable course URLs using React Router v6. Two routes:
  - `/` — course search page
  - `/courses/:courseId` — professor rankings for a specific course (courseId = database integer ID)
- **D-09:** `vercel.json` rewrite rule: `{ "source": "/(.*)", "destination": "/index.html" }` — required for React Router deep links to work on Vercel (per DEPLOY-01).
- **D-10:** Navigating to `/courses/142` directly (e.g., from a shared link) should load the course data from the API using the courseId param — the page must be self-sufficient without requiring the user to search first.

### Data Fetching
- **D-11:** Use **TanStack Query (react-query)** for all API calls. Reasons: built-in loading/error/success states, automatic caching (back-navigate to a course = instant re-render from cache, no refetch), automatic retry on failure, and clean `isLoading` state for the cold-start UX.
- **D-12:** Cold-start UX implementation: on the `/courses/:courseId` page, track elapsed time since the first API call. If `isLoading` is still true after 3 seconds, show the "Waking up the server…" message alongside the skeleton cards (per UI-11).

### Tech Scaffolding
- **D-13:** Vite + React as the build tool (localhost:5173 already set in Phase 2 CORS config). **TypeScript** — Claude's discretion on whether to use TS or JS; TS is the standard for new React projects and shadcn/ui's own templates use it.
- **D-14:** shadcn/ui + Tailwind CSS (Command component for autocomplete, Skeleton for loading, Sheet for mobile sliders, Collapsible for card expand).
- **D-15:** Recharts for both charts: `BarChart` for grade distribution (UI-03) and `LineChart` for GPA trend (UI-04). Both use `width="100%"` for responsive sizing (per UI-09).

### Claude's Discretion
- Color banding visual implementation (border, badge, or text color — pick the most polished option)
- Mobile slider UI (shadcn/ui Sheet is the obvious choice)
- Numeric weight display (show if it fits)
- TypeScript vs. JavaScript (TS recommended; follow shadcn/ui templates)
- Exact sidebar width and responsive breakpoint (Tailwind `md:` breakpoint standard)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Requirements
- `.planning/REQUIREMENTS.md` §React Frontend — UI-01 through UI-11 (all 11 requirements apply to this phase)
- `.planning/REQUIREMENTS.md` §Deployment — DEPLOY-01 (React Router + vercel.json rewrite — implemented in this phase)

### Existing Code to Wrap
- `api/routers/courses.py` — `GET /courses/search` and `GET /courses/{id}/professors` endpoints
- `api/routers/professors.py` — `GET /professors/{id}/grades` and `GET /professors/{id}/comments` endpoints
- `api/schemas.py` — Pydantic response models define exact JSON shape the React app must consume

### Reference Implementation
- `dashboard/app.py` — Streamlit prototype: reference for data layout, weight slider behavior, grade chart structure, comment rendering, and color-banding thresholds (≥70 green, 50–69 yellow, <50 red)

### Phase 2 Context (API design decisions)
- `.planning/phases/02-fastapi-backend/02-CONTEXT.md` §Score Computation Strategy — D-03: raw factors returned from API, weight sliders recompute client-side

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `dashboard/app.py` — complete Streamlit implementation: professor card structure, weight slider logic, chart setup, comment rendering, color-banding thresholds. Use as a blueprint for React component behavior.
- `etl/scoring.py:compute_gaucho_score()` — the scoring formula. The React app reimplements this in JavaScript for client-side recomputation when weights change: `score = gpa_f * w_gpa + quality_f * w_quality + difficulty_f * w_difficulty + sentiment_f * w_sentiment` (normalized weights).

### Established Patterns
- **API base URL**: `http://localhost:8000` in dev, Render URL in production — will need an environment variable (`VITE_API_URL`)
- **Session factory**: Phase 2 uses `localhost:5173` as the allowed CORS origin. The Vite dev server must run on port 5173 exactly.
- **Test database**: Phase 2 endpoint tests use SAVEPOINT isolation. Frontend has no test DB dependency — mock API responses with MSW or TanStack Query's test utilities.

### Integration Points
- `api/schemas.py` — professor ranking response includes `gaucho_score`, `gpa_factor`, `quality_factor`, `difficulty_factor`, `sentiment_factor` for client-side recomputation
- `api/main.py` — FastAPI app entry point (`uvicorn api.main:app --reload`) must be running for the React dev server to fetch data

</code_context>

<specifics>
## Specific Ideas

- Weight sliders recompute: `normalizedWeights = weights / sum(weights)`, then `score = Σ(factor * normalizedWeight)`. This mirrors `dashboard/app.py:50-54` exactly.
- The four weight labels should match the Streamlit labels: "GPA Weight", "Quality Weight", "Difficulty Weight", "Sentiment Weight"
- Grade distribution bar chart: 13 letter grades (A+, A, A-, B+, B, B-, C+, C, C-, D+, D, D-, F) on X-axis, student count on Y-axis — matches Streamlit implementation
- GPA trend line chart: Y-axis fixed at 0–4.0 range (per Streamlit `yaxis_range=[0, 4.0]`)
- VADER sentiment badge thresholds: ≥0.2 = Positive (green), ≤ -0.2 = Negative (red), else Neutral (orange) — matches Streamlit implementation
- `VITE_API_URL` environment variable for the FastAPI base URL — `.env.local` in dev, Vercel environment variable in production

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within Phase 3 scope.

</deferred>

---

*Phase: 03-react-frontend*
*Context gathered: 2026-04-01*

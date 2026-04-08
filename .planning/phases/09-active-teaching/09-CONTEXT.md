# Phase 9: Active Teaching - Context

**Gathered:** 2026-04-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Add "Actively Teaching" badges to professor cards, a filter toggle to show only active teachers, and a collapsible quarter history display. Requires backend changes (new query logic and API response fields) plus frontend component updates. A professor is "actively teaching" if they have 3+ distinct (quarter, year) entries in GradeDistribution for this course in the past 3 years.

</domain>

<decisions>
## Implementation Decisions

### Backend Logic
- Determine "past 3 years" by filtering GradeDistribution where `year >= current_year - 3` — uses existing `year` column
- Compute server-side in the professors ranking query — add `is_active_teacher` boolean and `recent_quarters` string array to the API response
- "3+ times" means 3+ distinct (quarter, year) entries in GradeDistribution for this professor+course in the past 3 years
- `recent_quarters` format: array of strings like `["Fall 2024", "Winter 2025", "Spring 2025"]` sorted most recent first

### Badge & Filter UI
- Small teal pill badge next to professor name: "Actively Teaching" — uses brand primary color (`bg-primary text-primary-foreground`)
- Toggle switch above the professor list: "Show only active teachers" — filters client-side from the full API response
- Collapsible section in professor card: "Quarters Taught (5)" → expands to show the list of quarters
- On mobile, the filter toggle lives in the same bottom Sheet as the weight toggles, above them

### Edge Cases
- If no professors are "active" for a course: show all professors (no filter applied), with a note "No professors have taught this course recently"
- Professors with 0 grade records: no badge, no quarter list — they still appear in ranking from RMP data
- Default filter state: OFF — show all professors by default, student opts in to filter

### Claude's Discretion
- Exact collapsible component (shadcn Collapsible or custom accordion)
- Toggle switch component choice (shadcn Switch or custom)
- SQL query structure for the active teaching computation
- Test structure and assertion patterns
- Exact positioning of badge relative to professor name

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `dashboard/queries.py` — `get_professors_for_course()` already computes `quarters_taught` via `count(GradeDistribution.id)` — needs enhancement
- `db/models.py` — `GradeDistribution` model has `quarter` (text), `year` (integer), `professor_id`, `course_id`
- `api/routers/courses.py` — professors endpoint returns ranking data, needs new fields
- `api/schemas.py` — Pydantic schemas for API responses
- `frontend/src/types/api.ts` — `ProfessorRanking` interface, needs new fields
- `frontend/src/components/ProfessorCard.tsx` — professor card component, add badge and quarter list

### Established Patterns
- Backend: SQLAlchemy queries in `dashboard/queries.py`, FastAPI routes in `api/routers/`
- Frontend: React components with Vitest tests, Tailwind styling, shadcn/ui primitives
- API contract: Python dict → Pydantic schema → JSON → TypeScript interface

### Integration Points
- `dashboard/queries.py:get_professors_for_course()` — add active teaching fields to query
- `api/schemas.py:ProfessorRanking` — add `is_active_teacher` and `recent_quarters` fields
- `api/routers/courses.py` — pass new fields through
- `frontend/src/types/api.ts:ProfessorRanking` — add new fields
- `frontend/src/components/ProfessorCard.tsx` — display badge and quarter list
- `frontend/src/pages/CoursePage.tsx` — add filter toggle and filter logic

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond the decisions above.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

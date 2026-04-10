# Phase 17: Schedule Display & Registration Context

**Gathered:** 2026-04-10
**Status:** Ready for planning
**Mode:** Auto-generated (frontend phase)

<domain>
## Phase Boundary

Display schedule data from Phase 16's backend on professor cards: "Teaching Next Quarter" badge with expandable section details, quarter filter for the professor list, and a registration countdown banner. Frontend-only changes consuming the new API fields.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation at Claude's discretion. Key requirements:

1. DISP-01: "Teaching Next Quarter" badge on professor cards (when teaching_next_quarter is true)
2. DISP-02: Expandable section details — day/time, building/room, seats (enrolled/max_enroll)
3. DISP-03: Quarter filter — "Next Quarter" / "Current Quarter" / "All" toggle above professor list
4. REG-01: Registration countdown banner — "Pass 1 opens in 3 days" when approaching
5. REG-02: Banner shows quarter name and link to GOLD (https://my.sa.ucsb.edu/gold/)

### API Fields Available (from Phase 16)
- `ProfessorRanking.teaching_next_quarter: boolean`
- `ProfessorRanking.scheduled_sections: ScheduledSectionResponse[]`
  - Each: quarter_code, quarter_name, enroll_code, instructor_name_raw, days, begin_time, end_time, building, room, enrolled, max_enroll

### New API Endpoint Needed
- `GET /quarters/current` — returns current quarter info + pass dates from UCSB Quarter Calendar API
- Frontend fetches this on app load for the registration countdown

### Design System
- Use Royal Blue + Snow (v2.0) design tokens
- Badge: similar to "Actively Teaching" but distinct — maybe blue outline variant
- Section details: inside a collapsible on the professor card
- Quarter filter: shadcn ToggleGroup or segmented control above professor list
- Registration banner: subtle top banner below navbar, dismissible

</decisions>

<code_context>
## Existing Code Insights

### Files to create/modify
- `frontend/src/types/api.ts` — add ScheduledSection interface, QuarterInfo interface
- `frontend/src/components/ProfessorCard.tsx` — add badge + section details
- `frontend/src/pages/CoursePage.tsx` — add quarter filter
- `frontend/src/components/RegistrationBanner.tsx` — new component
- `frontend/src/layouts/Layout.tsx` — render banner
- `frontend/src/hooks/useQuarterInfo.ts` — fetch quarter/pass data
- `frontend/src/lib/api.ts` — add fetchQuarterInfo()
- `api/routers/quarters.py` — new router for quarter info endpoint
- `api/main.py` — register quarters router

### Existing patterns
- Badges use shadcn Badge component
- Collapsibles use shadcn Collapsible
- React Query for data fetching
- MSW handlers for test mocking

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond the locked decisions.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>

---
phase: 09-active-teaching
plan: 02
subsystem: ui
tags: [active-teaching, badge, filter, collapsible, react, vitest, msw, tdd]
dependency_graph:
  requires:
    - phase: 09-01
      provides: is_active_teacher and recent_quarters backend fields on ProfessorRanking API
  provides:
    - "Actively Teaching" teal badge on ProfessorCard
    - "Show only active teachers" client-side filter toggle on CoursePage
    - Collapsible QuartersList component showing recent quarters taught
    - 8 frontend component tests (5 ProfessorCard + 3 CoursePage)
  affects: [frontend/src/components/ProfessorCard.tsx, frontend/src/pages/CoursePage.tsx, frontend/src/types/api.ts]
tech_stack:
  added: []
  patterns: [inline-subcomponent, client-side-filter-with-edge-case-fallback, tdd-red-green]
key_files:
  created:
    - frontend/src/components/__tests__/ProfessorCard.test.tsx
    - frontend/src/pages/__tests__/CoursePage.test.tsx
  modified:
    - frontend/src/types/api.ts
    - frontend/src/components/ProfessorCard.tsx
    - frontend/src/pages/CoursePage.tsx
    - frontend/src/test/mswHandlers.ts
    - frontend/src/components/ProfessorCard.test.tsx
    - frontend/src/components/CourseSearch.test.tsx
key_decisions:
  - "Used Checkbox (not Switch) for filter toggle since no switch.tsx exists in shadcn components"
  - "QuartersList as inline component within ProfessorCard.tsx rather than separate file"
  - "Fixed MSW handler URLs from localhost:8000 to localhost:8001 to match VITE_API_URL env"
patterns_established:
  - "ActiveTeacherFilter: reusable inline component placed in both desktop sidebar and mobile Sheet"
  - "Client-side filter with edge-case fallback: when filter active but no matches, show all with informational note"
requirements_completed: [TEACH-01, TEACH-02, TEACH-03]
metrics:
  duration: ~10 minutes
  completed: "2026-04-08"
  tasks_completed: 2
  tasks_total: 2
  tests_added: 8
  tests_total_passing: 95
---

# Phase 9 Plan 2: Active Teaching Frontend UI Summary

**"Actively Teaching" teal badge, collapsible quarter history, and client-side filter toggle with edge-case fallback on CoursePage, plus 8 TDD tests**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-04-08T05:31:33Z
- **Completed:** 2026-04-08T05:41:00Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Added `is_active_teacher: boolean` and `recent_quarters: string[]` to frontend ProfessorRanking TypeScript interface (mirrors backend Pydantic schema)
- Rendered "Actively Teaching" teal pill badge next to professor name when `is_active_teacher` is true
- Added collapsible "Quarters Taught (N)" section with outline badges for each quarter
- Added "Show only active teachers" checkbox filter on CoursePage -- desktop sidebar and mobile bottom Sheet, above weight toggles
- Edge case handled: when filter is on but no professors are active, all professors shown with a yellow informational note
- 8 new frontend component tests covering badge, quarter list, and filter toggle behavior
- All 95 tests pass, TypeScript compiles cleanly, production build succeeds

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Failing tests for badge, quarter list, filter** - `c36d8b8` (test)
2. **Task 1 GREEN: Implementation + all tests passing** - `1f5c1e6` (feat)

_Note: Task 2 (test creation) was fulfilled during Task 1's TDD cycle -- test files created in RED, verified in GREEN. No separate commit needed._

## Files Created/Modified

- `frontend/src/types/api.ts` - Added is_active_teacher and recent_quarters to ProfessorRanking interface
- `frontend/src/components/ProfessorCard.tsx` - Added QuartersList component, "Actively Teaching" badge, collapsible quarters section
- `frontend/src/pages/CoursePage.tsx` - Added ActiveTeacherFilter component, showActiveOnly state, filter logic in rankedProfessors memo, edge-case note
- `frontend/src/test/mswHandlers.ts` - Updated mock data with new fields, fixed URL to match VITE_API_URL
- `frontend/src/components/__tests__/ProfessorCard.test.tsx` - 5 tests: badge visibility, quarter list rendering, collapsible behavior
- `frontend/src/pages/__tests__/CoursePage.test.tsx` - 3 tests: filter default state, filter hides inactive, edge case note
- `frontend/src/components/ProfessorCard.test.tsx` - Added missing new fields to existing mock data
- `frontend/src/components/CourseSearch.test.tsx` - Fixed MSW URL to match VITE_API_URL

## Decisions Made

1. **Checkbox for filter toggle**: Used Checkbox component (not Switch) since no `switch.tsx` exists in the project's shadcn components. Follows the same pattern as WeightToggles.
2. **QuartersList as inline component**: Defined within ProfessorCard.tsx rather than a separate file, keeping related rendering logic colocated.
3. **MSW URL fix**: Corrected all MSW handlers from `http://localhost:8000` to `http://localhost:8001` to match `VITE_API_URL` in `.env`, fixing previously broken CourseSearch and CoursePage tests.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed MSW handler URLs mismatched with VITE_API_URL**
- **Found during:** Task 1 GREEN (CoursePage tests failing)
- **Issue:** MSW handlers used `http://localhost:8000` but `.env` sets `VITE_API_URL=http://localhost:8001`, causing unhandled request errors in tests
- **Fix:** Updated all MSW handler URLs and test `server.use()` overrides to `http://localhost:8001`
- **Files modified:** frontend/src/test/mswHandlers.ts, frontend/src/pages/__tests__/CoursePage.test.tsx, frontend/src/components/CourseSearch.test.tsx
- **Verification:** All 95 tests pass
- **Committed in:** 1f5c1e6 (Task 1 GREEN commit)

**2. [Rule 3 - Blocking] Fixed pre-existing ProfessorCard.test.tsx mock data**
- **Found during:** Task 1 GREEN (existing ProfessorCard tests failing)
- **Issue:** Existing `mockProfessor` in ProfessorCard.test.tsx missing new required `is_active_teacher` and `recent_quarters` fields after interface update
- **Fix:** Added `is_active_teacher: false, recent_quarters: []` to existing mock data
- **Files modified:** frontend/src/components/ProfessorCard.test.tsx
- **Verification:** All 9 ProfessorCard tests pass
- **Committed in:** 1f5c1e6 (Task 1 GREEN commit)

---

**Total deviations:** 2 auto-fixed (2 blocking issues)
**Impact on plan:** Both fixes necessary for tests to pass. MSW URL mismatch was a pre-existing bug surfaced by the new tests. No scope creep.

## Test Results

- 95/95 tests passing across 17 test files
- 8 new tests added (5 ProfessorCard + 3 CoursePage)
- Zero regressions

## Issues Encountered

None beyond the auto-fixed deviations above.

## Threat Surface Scan

No new threat surface introduced. The filter is client-side only (UI convenience), the badge is display-only, and the quarter list renders server-computed public academic data. No new network endpoints, auth paths, or file access patterns.

## Known Stubs

None -- all UI components are wired to real API response data (is_active_teacher and recent_quarters from backend).

## User Setup Required

None -- no external service configuration required.

## Next Phase Readiness

- Phase 9 (Active Teaching) is now complete: backend query (Plan 01) + frontend UI (Plan 02)
- Ready for Phase 10: Most-Recent-Quarter Grade Distribution

---
*Phase: 09-active-teaching*
*Completed: 2026-04-08*

## Self-Check: PASSED

- All 8 created/modified files verified on disk
- Both commits (c36d8b8, 1f5c1e6) verified in git log

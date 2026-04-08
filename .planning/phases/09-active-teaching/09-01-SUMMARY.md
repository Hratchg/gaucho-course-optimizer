---
phase: 09-active-teaching
plan: 01
subsystem: backend
tags: [active-teaching, query, schema, api, tdd]
dependency_graph:
  requires: []
  provides: [is_active_teacher, recent_quarters, active-teaching-api]
  affects: [dashboard/queries.py, api/schemas.py, api/routers/courses.py]
tech_stack:
  added: []
  patterns: [subquery-join, server-side-cutoff-year, quarter-sort-order]
key_files:
  created: []
  modified:
    - dashboard/queries.py
    - api/schemas.py
    - api/routers/courses.py
    - tests/test_dashboard_queries.py
    - tests/test_courses_router.py
decisions:
  - "Used two-level subquery (GROUP BY quarter/year then COUNT) for distinct pair counting rather than string concatenation"
  - "Separate 3rd query for recent_quarters detail (like existing keywords pattern) to avoid complicating the main query GROUP BY"
  - "Server-side cutoff_year = datetime.now().year - 3 per T-09-02 threat mitigation"
metrics:
  duration: ~7 minutes
  completed: "2026-04-08"
  tasks_completed: 1
  tasks_total: 1
  tests_added: 6
  tests_total_passing: 22
---

# Phase 9 Plan 1: Active Teaching Backend Query Summary

Active teaching subquery computing is_active_teacher (bool) and recent_quarters (sorted string list) added to get_professors_for_course, with schema and router passthrough and 6 new TDD tests.

## What Was Done

### Task 1: Active teaching subquery + recent_quarters + schema + router + tests (TDD)

**RED phase** (commit `b3998b8`):
- Added 5 query-level tests in `tests/test_dashboard_queries.py`:
  - `test_active_teacher_true` -- 3+ distinct (quarter, year) in 3-year window
  - `test_active_teacher_false` -- 2 distinct pairs, below threshold
  - `test_active_teacher_old_records_excluded` -- all records older than cutoff
  - `test_recent_quarters_sorted_most_recent_first` -- descending sort by year then quarter
  - `test_recent_quarters_format` -- "Quarter Year" string format
- Added 1 router-level test in `tests/test_courses_router.py`:
  - `test_professor_response_includes_active_teaching_fields` -- response JSON contains both new fields
- Updated `_make_prof` helper with `is_active_teacher` and `recent_quarters` defaults

**GREEN phase** (commit `455c1c6`):
- Enhanced `dashboard/queries.py:get_professors_for_course()`:
  - Added `cutoff_year = datetime.now().year - 3` (server-side, not client-controllable)
  - Added `recent_grades_sq` subquery grouping by (professor_id, quarter, year) for recent records
  - Added `active_teaching_sq` wrapper counting distinct quarter-year pairs per professor
  - Left-joined active_teaching_sq into main query
  - Added 3rd query for `recent_quarters` detail sorted by year desc, then quarter order (Fall > Summer > Spring > Winter)
  - Each professor dict now includes `is_active_teacher` (bool) and `recent_quarters` (list[str])
- Extended `api/schemas.py:ProfessorRanking` with `is_active_teacher: bool = False` and `recent_quarters: list[str] = []`
- Updated `api/routers/courses.py` to pass through both new fields via `p.get()`

## Test Results

- 22/22 tests passing in target files (5 new query + 1 new router + 16 pre-existing)
- Full suite: 114 passed, 1 pre-existing error (missing pytest-mock fixture in test_rmp_scraper.py -- unrelated)
- Zero regressions

## Deviations from Plan

None -- plan executed exactly as written.

## Decisions Made

1. **Two-level subquery for distinct counting**: Used GROUP BY (professor_id, quarter, year) then COUNT(*) rather than string concatenation with func.concat. Cleaner and avoids type-casting edge cases.
2. **Separate 3rd query for quarter detail**: Follows the existing keywords pattern (batch query after main query) rather than trying to aggregate string arrays in the main query GROUP BY.
3. **Server-side cutoff_year**: Computed from `datetime.now().year - 3` per T-09-02 threat mitigation -- client cannot manipulate the time window.

## Threat Surface Scan

No new threat surface introduced. The `cutoff_year` is computed server-side (mitigates T-09-02). The `recent_quarters` data is public academic information (T-09-01 accepted). No new endpoints, auth paths, or file access patterns were added.

## Known Stubs

None -- all fields are wired to real query data.

## Self-Check: PASSED

- All 6 modified/created files verified on disk
- Both commits (b3998b8, 455c1c6) verified in git log

---
phase: 06-navigation-routing
plan: 01
subsystem: ui
tags: [react-router, navbar, layout, navigation, tailwind]

# Dependency graph
requires:
  - phase: 05-branding-design-system
    provides: Design tokens (--primary, --accent, --font-heading), Poppins + Open Sans fonts
provides:
  - Navbar component with sticky positioning, brand wordmark, NavLink active states
  - Layout.tsx shell with Navbar + Outlet for persistent nav across all pages
  - HomePage placeholder with hero heading and CTA linking to /search
  - Route structure: / (Home), /search (Search), /courses/:courseId (Course Results)
  - CourseSearch passes courseCode via router state for breadcrumb use
affects: [06-02-breadcrumbs-mobile-menu, 07-tutorial-landing-page]

# Tech tracking
tech-stack:
  added: []
  patterns: [Layout+Outlet route nesting, NavLink className callback for active state, router state for cross-page data]

key-files:
  created:
    - frontend/src/components/Navbar.tsx
    - frontend/src/components/Navbar.test.tsx
    - frontend/src/pages/HomePage.tsx
    - frontend/src/pages/HomePage.test.tsx
    - frontend/src/layouts/Layout.tsx
  modified:
    - frontend/src/App.tsx
    - frontend/src/pages/SearchPage.tsx
    - frontend/src/components/CourseSearch.tsx
    - frontend/src/pages/CoursePage.tsx

key-decisions:
  - "Navbar children prop with MobileMenuSlot div for Plan 02 hamburger injection"
  - "NavLink end prop on / route for explicit exact-match active detection"
  - "top-20 (80px) sticky sidebar offset for CoursePage = 56px navbar + 24px gap"

patterns-established:
  - "Layout+Outlet: All routes wrapped in Layout.tsx for persistent navbar shell"
  - "NavLink active state: className callback returning font-bold text-white when isActive"
  - "Router state forwarding: navigate with { state: { courseCode } } for breadcrumb display"

requirements-completed: [NAV-01, NAV-04]

# Metrics
duration: 5min
completed: 2026-04-07
---

# Phase 6 Plan 01: Layout, Navbar, and Route Structure Summary

**Persistent Layout shell with sticky Navbar, placeholder HomePage with accent CTA, and restructured App.tsx routing (/, /search, /courses/:courseId) using React Router Outlet pattern**

## Performance

- **Duration:** 5 min
- **Started:** 2026-04-07T22:24:12Z
- **Completed:** 2026-04-07T22:29:36Z
- **Tasks:** 2
- **Files modified:** 9 (5 created, 4 modified)

## Accomplishments
- Sticky Navbar with brand wordmark ("Gaucho Course Optimizer" in accent color), Home/Search NavLinks with active state, and mobile menu slot for Plan 02
- Placeholder HomePage with hero heading, subtext, and accent-colored "Start Searching" CTA button
- Layout.tsx wrapping all routes via Outlet, rendering Navbar persistently on every page
- App.tsx restructured: / renders HomePage, /search renders SearchPage, /courses/:courseId renders CoursePage
- CourseSearch passes courseCode via router state for breadcrumb display in Plan 02
- CoursePage sticky sidebar offset fixed from top-6 to top-20 to account for navbar height

## Task Commits

Each task was committed atomically:

1. **Task 1: Create Navbar and HomePage components (TDD)**
   - `cef850c` (test) - Failing tests for Navbar and HomePage
   - `c685241` (feat) - Navbar and HomePage implementation, all 8 tests green
2. **Task 2: Restructure App.tsx routes with Layout wrapper** - `3fd4a93` (feat)

## Files Created/Modified
- `frontend/src/components/Navbar.tsx` - Sticky top navbar with brand wordmark, NavLinks, mobile menu slot
- `frontend/src/components/Navbar.test.tsx` - 5 tests: brand text, nav links, active state, brand link
- `frontend/src/pages/HomePage.tsx` - Placeholder home with hero heading, subtext, CTA to /search
- `frontend/src/pages/HomePage.test.tsx` - 3 tests: heading, CTA link, document.title
- `frontend/src/layouts/Layout.tsx` - min-h-screen flex-col shell with Navbar + Outlet
- `frontend/src/App.tsx` - Layout wrapper with three nested child routes
- `frontend/src/pages/SearchPage.tsx` - Removed old GCO heading, replaced with "Search Courses"
- `frontend/src/components/CourseSearch.tsx` - Added courseCode router state to navigate call
- `frontend/src/pages/CoursePage.tsx` - Sticky sidebar offset changed from top-6 to top-20

## Decisions Made
- Navbar accepts children prop with a `flex md:hidden` slot div for MobileMenu injection in Plan 02 -- avoids modifying Navbar when adding hamburger menu
- Used `end` prop on NavLink to="/" for explicit exact-match even though v7 special-cases root
- Set CoursePage sidebar to `top-20` (80px = 56px navbar + 24px original gap) rather than a calc expression for simplicity

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] npm install required in worktree**
- **Found during:** Pre-task setup
- **Issue:** Worktree had no node_modules directory; vitest could not run
- **Fix:** Ran `npm install` in the frontend directory
- **Files modified:** none committed (node_modules is gitignored)
- **Verification:** `npx vitest run` succeeds with 43 existing tests passing

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Standard worktree setup. No scope creep.

## Issues Encountered
None -- all changes worked as planned on first implementation.

## User Setup Required
None - no external service configuration required.

## Verification Results
- `npx vitest run` -- 51 tests pass (43 existing + 8 new), 13 test files, zero failures
- `npx tsc --noEmit` -- clean, no TypeScript errors
- `npm run build` -- production build succeeds

## Next Phase Readiness
- Layout shell ready for Breadcrumbs component injection (Plan 02 adds between Navbar and Outlet)
- Navbar children prop ready for MobileMenu hamburger button injection (Plan 02)
- CourseSearch router state ready for Breadcrumbs to read courseCode (Plan 02)
- HomePage is a lightweight placeholder -- will be replaced entirely by Phase 7 Tutorial Landing Page

## Self-Check: PASSED

All 5 created files verified on disk. All 3 commit hashes (cef850c, c685241, 3fd4a93) found in git log.

---
*Phase: 06-navigation-routing*
*Completed: 2026-04-07*

---
phase: 06-navigation-routing
plan: 02
subsystem: ui
tags: [breadcrumbs, mobile-menu, sheet, navigation, accessibility]

# Dependency graph
requires:
  - phase: 06-01
    provides: Layout.tsx shell with Navbar + Outlet, Navbar with mobile slot, CourseSearch router state with courseCode
provides:
  - Breadcrumbs component with route-conditional rendering and courseCode from router state
  - MobileMenu component with Sheet drawer, auto-close on link click, 44px touch targets
  - Complete navigation system (Navbar + Breadcrumbs + MobileMenu) across all three pages
affects: [07-tutorial-landing-page]

# Tech tracking
tech-stack:
  added: []
  patterns: [Fragment for flat list rendering, SheetClose asChild for auto-close, NavLink className callback in Sheet, aria-describedby suppression for Radix Dialog]

key-files:
  created:
    - frontend/src/components/Breadcrumbs.tsx
    - frontend/src/components/Breadcrumbs.test.tsx
    - frontend/src/components/MobileMenu.tsx
    - frontend/src/components/MobileMenu.test.tsx
  modified:
    - frontend/src/layouts/Layout.tsx
    - frontend/src/components/Navbar.tsx

key-decisions:
  - "Breadcrumbs uses useLocation() pathname matching (not useParams) for route detection -- works at Layout level where params are unavailable"
  - "Navbar changed from children prop to direct MobileMenu import -- simpler integration, no prop drilling needed"
  - "aria-describedby={undefined} on SheetContent to suppress Radix Dialog description warning -- Sheet navigation menu does not need a description"

patterns-established:
  - "Fragment-based flat list: Use React Fragment instead of wrapper li to avoid nested li DOM violations"
  - "SheetClose asChild + NavLink: Wrap navigation links in SheetClose for auto-close on click without controlled state"

requirements-completed: [NAV-02, NAV-03]

# Metrics
duration: 6min
completed: 2026-04-07
---

# Phase 6 Plan 02: Breadcrumbs and Mobile Menu Summary

**Route-conditional breadcrumb trail (Home > Search > Course Code) using useLocation pathname matching, plus Sheet-based mobile hamburger menu with SheetClose asChild auto-close and 44px WCAG touch targets**

## Performance

- **Duration:** 6 min
- **Started:** 2026-04-07T22:34:14Z
- **Completed:** 2026-04-07T22:40:00Z
- **Tasks:** 2 completed, 1 checkpoint (human-verify)
- **Files modified:** 6 (4 created, 2 modified)

## Accomplishments

- Breadcrumbs component renders conditionally: null on /, "Home > Search" on /search, "Home > Search > {courseCode}" on /courses/:id
- Reads courseCode from router state (set by CourseSearch navigate) with "Course Results" fallback for direct URL access
- Full accessibility: nav aria-label="Breadcrumb", ol list structure, aria-hidden separators, aria-current="page" on active item
- Active breadcrumb styled with text-accent font-medium (amber), inactive with text-muted-foreground hover:text-foreground
- Layout.tsx updated to render Breadcrumbs between Navbar and main/Outlet
- MobileMenu with Sheet sliding from right, hamburger button with 44px minimum touch target
- Two nav links (Home, Search) wrapped in SheetClose asChild for auto-close on navigation
- NavLink className callback in Sheet for active state (font-bold text-primary)
- SheetTitle "Gaucho Course Optimizer" in font-heading font-bold
- Navbar.tsx refactored: removed children prop, imports MobileMenu directly in flex md:hidden slot

## Task Commits

Each task was committed atomically (TDD RED + GREEN):

1. **Task 1: Create Breadcrumbs component and wire into Layout (TDD)**
   - `2c4e99a` (test) - 8 failing tests for route-conditional breadcrumbs
   - `3117b77` (feat) - Breadcrumbs implementation + Layout integration, all 8 tests green

2. **Task 2: Create MobileMenu component and wire into Navbar (TDD)**
   - `9d63ac8` (test) - 5 failing tests for Sheet-based mobile menu
   - `8bdbff3` (feat) - MobileMenu implementation + Navbar integration, all 5 tests green

3. **Task 3: Visual verification** - checkpoint:human-verify (pending)

## Files Created/Modified

- `frontend/src/components/Breadcrumbs.tsx` - Route-conditional breadcrumb trail with useLocation, ChevronRight separators, accessible markup
- `frontend/src/components/Breadcrumbs.test.tsx` - 8 tests: route rendering, state/fallback, accessibility, CSS classes
- `frontend/src/components/MobileMenu.tsx` - Sheet-based mobile drawer with hamburger trigger, NavLink active states, SheetClose auto-close
- `frontend/src/components/MobileMenu.test.tsx` - 5 tests: button rendering, touch target, Sheet open/close, link navigation
- `frontend/src/layouts/Layout.tsx` - Added Breadcrumbs import and render between Navbar and Outlet
- `frontend/src/components/Navbar.tsx` - Replaced children prop with direct MobileMenu import in mobile slot

## Decisions Made

- Breadcrumbs uses `useLocation().pathname` for route detection rather than `useParams()`, because params are not available in Layout-level components
- Navbar refactored from children-based composition to direct import of MobileMenu -- cleaner integration since the mobile slot is always MobileMenu
- Added `aria-describedby={undefined}` to SheetContent to suppress Radix Dialog accessibility warning, since the navigation Sheet does not need a description

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed nested li DOM violation in Breadcrumbs**
- **Found during:** Task 1 GREEN phase
- **Issue:** Initial implementation used `<li className="contents">` as wrapper with inner `<li>` elements, causing React DOM nesting warning
- **Fix:** Replaced wrapper `<li>` with React `<Fragment>` for flat list structure
- **Files modified:** frontend/src/components/Breadcrumbs.tsx
- **Commit:** 3117b77

**2. [Rule 2 - Missing accessibility] Added aria-describedby suppression on SheetContent**
- **Found during:** Task 2 GREEN phase
- **Issue:** Radix Dialog warned about missing Description or aria-describedby on SheetContent
- **Fix:** Added `aria-describedby={undefined}` to SheetContent to explicitly suppress warning
- **Files modified:** frontend/src/components/MobileMenu.tsx
- **Commit:** 8bdbff3

**3. [Rule 3 - Blocking] npm install required in worktree**
- **Found during:** Pre-task setup
- **Issue:** Worktree had no node_modules directory
- **Fix:** Ran `npm install` in the frontend directory
- **Files modified:** none committed (node_modules is gitignored)

---

**Total deviations:** 3 auto-fixed (1 bug, 1 accessibility, 1 blocking)
**Impact on plan:** No scope creep. All fixes are correctness improvements.

## Issues Encountered

None -- all implementations worked with minor auto-fixes on first attempt.

## User Setup Required

None - no external service configuration required.

## Verification Results

- `npx vitest run --reporter=verbose` -- 64 tests pass (51 existing + 8 Breadcrumbs + 5 MobileMenu), 15 test files, zero failures
- `npx tsc --noEmit` -- clean, no TypeScript errors
- `npm run build` -- production build succeeds
- Manual verification pending (Task 3 checkpoint)

## Next Phase Readiness

- Complete navigation system ready: Navbar + Breadcrumbs + MobileMenu across all routes
- Phase 7 (Tutorial Landing Page) can replace HomePage.tsx without affecting navigation structure
- All navigation components are self-contained with clean interfaces

## Self-Check: PASSED

All 6 files verified on disk. All 4 commit hashes (2c4e99a, 3117b77, 9d63ac8, 8bdbff3) found in git log.

---
*Phase: 06-navigation-routing*
*Completed: 2026-04-07*

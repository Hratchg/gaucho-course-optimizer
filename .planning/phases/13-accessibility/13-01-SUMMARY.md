---
phase: 13-accessibility
plan: 01
subsystem: ui
tags: [accessibility, wcag, aria, focus-ring, reduced-motion, skip-link]

# Dependency graph
requires:
  - phase: 12-design-tokens
    provides: Royal Blue oklch palette and CSS custom properties
provides:
  - Skip-to-content link in Layout.tsx
  - Global .focusable focus-visible utility class
  - prefers-reduced-motion blanket media query
  - aria-labels on all collapsible triggers and chart
  - No duplicate main landmarks (CoursePage main -> section)
affects: [14-animations, 15-component-overhaul]

# Tech tracking
tech-stack:
  added: []
  patterns: [focusable CSS class for custom interactive elements, skip-to-content sr-only pattern, figure role="img" for chart a11y]

key-files:
  created: []
  modified:
    - frontend/src/index.css
    - frontend/src/layouts/Layout.tsx
    - frontend/src/components/Navbar.tsx
    - frontend/src/components/MobileMenu.tsx
    - frontend/src/components/Breadcrumbs.tsx
    - frontend/src/components/ProfessorCard.tsx
    - frontend/src/components/CourseSearch.tsx
    - frontend/src/components/GradeChart.tsx
    - frontend/src/pages/CoursePage.tsx

key-decisions:
  - "Used .focusable CSS class instead of Tailwind utilities for custom elements — shadcn components already have built-in focus-visible styles"
  - "prefers-reduced-motion uses 0.01ms duration (not 0s) to prevent issues with animation-end event listeners"
  - "Changed CoursePage nested main to section to avoid duplicate main landmarks for screen readers"

patterns-established:
  - "focusable class: Add .focusable to any custom interactive element (non-shadcn) for consistent 2px focus ring"
  - "Skip-to-content: First focusable child in Layout, targets #main-content with tabIndex={-1}"
  - "Chart accessibility: Wrap charts in figure with role='img' and descriptive aria-label"

requirements-completed: [A11Y-01, A11Y-02, A11Y-03, A11Y-04, A11Y-05, A11Y-06]

# Metrics
duration: 3min
completed: 2026-04-10
---

# Phase 13 Plan 01: Accessibility Summary

**WCAG AA accessibility layer with skip-to-content link, visible focus rings on all interactive elements, aria-labels on collapsible triggers and charts, and prefers-reduced-motion blanket rule**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-10T00:43:19Z
- **Completed:** 2026-04-10T00:46:04Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Skip-to-content link as first focusable element, visually hidden until focused, jumps to #main-content
- Global .focusable:focus-visible utility class with 2px ring for all custom interactive elements
- prefers-reduced-motion media query disables all animations (covers existing .animate-shake and future Phase 14 animations)
- aria-labels on ProfessorCard CollapsibleTriggers and CourseSearch Command component
- GradeChart wrapped in accessible figure with role="img" and descriptive aria-label
- Eliminated duplicate main landmarks by changing CoursePage nested main to section

## Task Commits

Each task was committed atomically:

1. **Task 1: Skip-to-content link, global focus ring styles, and reduced-motion support** - `4678380` (feat)
2. **Task 2: Aria-labels, focus rings, and keyboard navigation audit across all components** - `9daf196` (feat)

## Files Created/Modified
- `frontend/src/index.css` - Added .skip-to-content, .focusable:focus-visible, and prefers-reduced-motion media query
- `frontend/src/layouts/Layout.tsx` - Added skip-to-content link and id="main-content" on main element
- `frontend/src/components/Navbar.tsx` - Added focusable class to logo link and nav links
- `frontend/src/components/MobileMenu.tsx` - Added focusable class to hamburger button
- `frontend/src/components/Breadcrumbs.tsx` - Added focusable class to breadcrumb links
- `frontend/src/components/ProfessorCard.tsx` - Added aria-label and focusable class to both CollapsibleTriggers
- `frontend/src/components/CourseSearch.tsx` - Added label prop to Command for screen reader context
- `frontend/src/components/GradeChart.tsx` - Wrapped chart in figure with role="img" and aria-label
- `frontend/src/pages/CoursePage.tsx` - Changed nested main to section with aria-label

## Decisions Made
- Used .focusable CSS class instead of Tailwind utilities for custom elements -- shadcn components already have built-in focus-visible styles, so this only applies to raw HTML elements
- prefers-reduced-motion uses 0.01ms duration (not 0s) to prevent issues with animation-end event listeners
- Changed CoursePage nested main to section to avoid duplicate main landmarks for screen readers
- WeightToggles audited but unchanged -- shadcn Checkbox already has proper focus-visible styles and htmlFor label associations

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Accessibility infrastructure is in place before Phase 14 (animations)
- prefers-reduced-motion blanket rule will automatically cover any animations added in Phase 14
- .focusable class available for any new interactive elements in future phases

## Self-Check: PASSED

All 9 modified files verified present. Both task commits (4678380, 9daf196) verified in git log. All must_have content patterns (prefers-reduced-motion, skip-to-content, aria-label, focus-visible, #main-content) confirmed present in their target files.

---
*Phase: 13-accessibility*
*Completed: 2026-04-10*

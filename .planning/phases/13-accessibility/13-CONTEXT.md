# Phase 13: Accessibility - Context

**Gathered:** 2026-04-09
**Status:** Ready for planning
**Mode:** Auto-generated (cross-cutting infrastructure phase)

<domain>
## Phase Boundary

Add WCAG AA accessibility across the entire app: contrast verification, visible focus rings, aria-labels on all icon-only buttons, full keyboard navigation, skip-to-content link, and prefers-reduced-motion support. Cross-cutting changes touching Layout, Navbar, MobileMenu, ProfessorCard, CourseSearch, WeightToggles, and all interactive elements.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — infrastructure phase. Key requirements from ROADMAP:

1. All text meets WCAG AA contrast (4.5:1 normal, 3:1 large) — verify with new Royal Blue palette
2. Visible focus rings (2-4px) on ALL interactive elements — buttons, links, inputs, toggles, checkboxes
3. aria-labels on icon-only buttons: hamburger menu, close buttons, collapsible triggers, chart controls
4. Keyboard navigation: tab order matches visual order, Enter/Space activates buttons/links
5. Skip-to-content link: first focusable element on page, jumps past navbar to main content
6. prefers-reduced-motion: wrap all non-essential animations in a media query check

Use the UI/UX Pro Max guidelines:
- Focus rings: 2-4px, visible in both light and dark contexts
- aria-labels must be descriptive ("Open navigation menu" not just "menu")
- Skip link can be visually hidden until focused (sr-only + focus:not-sr-only pattern)
- Tab order: ensure no focus traps in Sheet/Collapsible components

</decisions>

<code_context>
## Existing Code Insights

### Components needing a11y audit
- `frontend/src/components/Navbar.tsx` — nav links need proper focus states
- `frontend/src/components/MobileMenu.tsx` — hamburger button needs aria-label, Sheet focus management
- `frontend/src/components/ProfessorCard.tsx` — collapsible triggers need aria-expanded, aria-labels
- `frontend/src/components/WeightToggles.tsx` — checkboxes already have labels, verify focus rings
- `frontend/src/components/CourseSearch.tsx` — Command component, verify keyboard navigation
- `frontend/src/components/GradeChart.tsx` — chart needs aria description
- `frontend/src/layouts/Layout.tsx` — add skip-to-content link and main landmark
- `frontend/src/pages/CoursePage.tsx` — filter toggle needs label

### Established Patterns
- shadcn/ui components generally include good a11y defaults (Radix primitives)
- Focus ring already partially defined via `outline-ring/50` in index.css @layer base
- Tailwind: use `focus-visible:ring-2 focus-visible:ring-primary` pattern

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond WCAG AA compliance.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>

# Phase 15: Component Overhaul - Context

**Gathered:** 2026-04-09
**Status:** Ready for planning
**Mode:** Auto-generated (visual refresh phase)

<domain>
## Phase Boundary

Redesign every user-facing component using the new Royal Blue + Snow tokens (Phase 12), accessibility patterns (Phase 13), and animation primitives (Phase 14). Every card, badge, nav element, chart, and page section gets the visual refresh. This is the culminating phase — after this, the v2.0 redesign is complete.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All visual refinements at Claude's discretion. Requirements from ROADMAP (COMP-01 through COMP-08):

1. COMP-01: Professor cards — new spacing, Royal Blue accents, Inter typography, hover elevation, staggered entrance
2. COMP-02: Navbar — Royal Blue background, Inter font, consistent link styling
3. COMP-03: Breadcrumbs — new accent colors (#DBEAFE border, #2563EB active link)
4. COMP-04: Course search — Royal Blue focus ring, Inter typography, updated dropdown styling
5. COMP-05: Grade charts — blue palette bars/lines, improved axis labels, consistent font
6. COMP-06: Mobile menu (Sheet) — new design tokens, Inter typography
7. COMP-07: Tutorial landing page — full redesign with Royal Blue accents, updated score breakdown, Inter
8. COMP-08: All badges (score, active teaching, tags) — new palette, consistent styling

Use Phase 12 tokens for colors, Phase 13 a11y patterns for focus/aria, Phase 14 animations for hover/press/entrance.

</decisions>

<code_context>
## Existing Code Insights

### All components to touch
- frontend/src/components/ProfessorCard.tsx (COMP-01)
- frontend/src/components/Navbar.tsx (COMP-02)
- frontend/src/components/Breadcrumbs.tsx (COMP-03)
- frontend/src/components/CourseSearch.tsx (COMP-04)
- frontend/src/components/GradeChart.tsx (COMP-05)
- frontend/src/components/GpaTrendChart.tsx (COMP-05)
- frontend/src/components/MobileMenu.tsx (COMP-06)
- frontend/src/pages/HomePage.tsx (COMP-07)
- frontend/src/components/SentimentBadge.tsx (COMP-08)
- frontend/src/components/WeightToggles.tsx (styling updates)
- frontend/src/pages/CoursePage.tsx (layout refinements)
- frontend/src/pages/SearchPage.tsx (styling updates)

### Foundation already in place
- Royal Blue + Snow tokens in index.css (Phase 12)
- Focus rings + skip-to-content + aria-labels (Phase 13)
- Animation utilities: .btn-press, .card-hover, .shimmer, .stagger-in, .page-enter (Phase 14)

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond applying the established design system cohesively.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>

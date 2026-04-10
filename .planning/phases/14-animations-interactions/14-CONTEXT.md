# Phase 14: Animations & Interactions - Context

**Gathered:** 2026-04-09
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase)

<domain>
## Phase Boundary

Build micro-interaction primitives: button press feedback, card hover elevation, page transitions, staggered professor list entrance, and skeleton shimmer loading. All animations must respect prefers-reduced-motion (Phase 13). Reusable CSS utilities and React hooks — consumed by Phase 15 component overhaul.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation specifics at Claude's discretion. Key specs from ROADMAP:

1. Button press: scale(0.97) + subtle shadow change, 150ms duration
2. Card hover: elevated shadow lift, 200ms ease-out, returns on mouse leave
3. Page transitions: fade + subtle vertical slide, 200ms — use CSS transitions or framer-motion-lite approach
4. Staggered list: 30-50ms delay between each professor card entrance — CSS animation-delay or IntersectionObserver
5. Skeleton shimmer: animated gradient sweep replacing static gray skeletons

All animations wrapped in prefers-reduced-motion check from Phase 13.
Use CSS @keyframes + Tailwind utilities where possible — avoid heavy JS animation libraries.

</decisions>

<code_context>
## Existing Code Insights

### Files to create/modify
- `frontend/src/index.css` — @keyframes for shimmer, stagger, press feedback
- `frontend/src/components/SkeletonCard.tsx` — add shimmer animation
- `frontend/src/components/ui/button.tsx` — add press feedback classes (or wrapper)
- `frontend/src/components/ProfessorCard.tsx` — add hover elevation + stagger delay
- `frontend/src/App.tsx` or Layout — page transition wrapper

### Existing animations
- `@keyframes shake` already in index.css (from Phase 8 weight toggles)
- prefers-reduced-motion media query added in Phase 13

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond the ROADMAP specs.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>

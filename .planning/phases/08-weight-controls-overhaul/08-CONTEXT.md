# Phase 8: Weight Controls Overhaul - Context

**Gathered:** 2026-04-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace the numeric weight sliders with four toggle checkboxes. Selected factors share weight equally (e.g., 2 enabled = 50% each). The professor ranking updates instantly in the browser on every toggle. No backend changes, no new API calls — purely frontend scoring logic and component replacement.

</domain>

<decisions>
## Implementation Decisions

### Toggle Checkbox Design
- Use shadcn/ui Checkbox with label text — clean, accessible, brand-consistent
- All 4 checkboxes ON by default (equal 25% each) — shows full ranking immediately on page load
- Small text below checkboxes showing dynamic weight distribution: "Each factor: 50%" (updates as toggles change)
- At least 1 checkbox must stay on — if user tries to uncheck last one, it stays checked with a subtle shake animation
- Labels: "Easy Grades", "Great Teaching", "Low Difficulty", "Good Reviews" (from ROADMAP success criteria)

### Scoring Logic & Layout
- Create new `WeightToggles.tsx` replacing `WeightSliders.tsx` — same sidebar/Sheet locations in CoursePage
- Update `computeScore` in `scoring.ts` to accept a boolean map `{gpa: true, quality: false, ...}` and divide weight equally among enabled factors
- Component heading: "Customize Ranking" — action-oriented, matches tutorial guide language
- Unchecked factors use muted text (text-muted-foreground) — clearly de-emphasized but still readable
- Remove old WeightSliders component and Slider UI dependency if no longer used

### Claude's Discretion
- Shake animation implementation (CSS keyframe or Tailwind animate)
- Exact layout of checkboxes (vertical stack vs 2x2 grid)
- Whether to keep or remove the old normalizeWeights function
- Test structure and assertion patterns

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/src/lib/scoring.ts` — `computeScore()` and `normalizeWeights()` functions, `Weights` and `DEFAULT_WEIGHTS` types
- `frontend/src/components/WeightSliders.tsx` — current slider component to replace
- `frontend/src/components/WeightSliders.test.tsx` — existing tests to update/replace
- shadcn/ui Checkbox available (may need to add via `npx shadcn@latest add checkbox`)
- CoursePage already has mobile Sheet integration for weight controls

### Established Patterns
- CoursePage uses `useState<Weights>` for weight state, passed as prop to WeightSliders
- `computeScore` called in `useMemo` with weights dependency — reranking is already instant
- Desktop: sidebar with sticky positioning; Mobile: bottom Sheet with "Adjust weights" button

### Integration Points
- `frontend/src/pages/CoursePage.tsx` — swap WeightSliders import for WeightToggles, update state type
- `frontend/src/lib/scoring.ts` — update computeScore signature and logic
- `frontend/src/lib/scoring.test.ts` — update scoring tests for boolean weights

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond the decisions above.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---
phase: 08-weight-controls-overhaul
plan: 01
subsystem: frontend-scoring-ui
tags: [toggles, scoring, ui-component, cleanup]
dependency_graph:
  requires: []
  provides: [WeightToggles, ToggleWeights, normalizeToggles, DEFAULT_TOGGLE_WEIGHTS]
  affects: [CoursePage, scoring]
tech_stack:
  added: [shadcn-checkbox, radix-checkbox]
  patterns: [boolean-toggle-weights, equal-share-distribution, last-toggle-guard]
key_files:
  created:
    - frontend/src/components/WeightToggles.tsx
    - frontend/src/components/WeightToggles.test.tsx
    - frontend/src/components/ui/checkbox.tsx
  modified:
    - frontend/src/lib/scoring.ts
    - frontend/src/lib/scoring.test.ts
    - frontend/src/pages/CoursePage.tsx
    - frontend/src/index.css
  deleted:
    - frontend/src/components/WeightSliders.tsx
    - frontend/src/components/WeightSliders.test.tsx
    - frontend/src/components/ui/slider.tsx
decisions:
  - Used union type (Weights | ToggleWeights) with typeof check for backward-compatible computeGauchoScore
  - Kept existing Weights type, DEFAULT_WEIGHTS, and normalizeWeights for backward compatibility
  - Used CSS keyframe animation (not Tailwind animate plugin) for shake effect
  - Vertical stack layout for checkboxes (simpler than 2x2 grid)
metrics:
  duration: 5m 22s
  completed: "2026-04-08T00:55:00Z"
  tasks_completed: 2
  tasks_total: 2
  tests_added: 17
  tests_total: 51
  files_changed: 10
---

# Phase 8 Plan 1: Weight Controls Overhaul Summary

Toggle checkboxes replacing sliders with ToggleWeights type, normalizeToggles for equal-share distribution, last-toggle guard with shake animation, and full CoursePage integration.

## Task Completion

| Task | Name | Commit | Status |
|------|------|--------|--------|
| 1 | Update scoring logic for boolean toggle weights + add Checkbox component | d9c21ce | Complete |
| 2 | Create WeightToggles component, integrate into CoursePage, clean up old slider code | 2a29263 | Complete |

## What Was Built

### Scoring Logic (Task 1)
- **ToggleWeights interface** with boolean fields (gpa, quality, difficulty, sentiment)
- **DEFAULT_TOGGLE_WEIGHTS** constant with all four set to `true`
- **normalizeToggles()** function converting boolean map to equal-share numeric weights (e.g., 2 enabled = 0.5 each, disabled = 0)
- **computeGauchoScore()** updated to accept both `Weights` (numeric) and `ToggleWeights` (boolean) via union type with runtime type detection -- full backward compatibility preserved
- **shadcn Checkbox** primitive added via `npx shadcn@latest add checkbox`
- 9 new tests added (normalizeToggles: 4, computeGauchoScore with ToggleWeights: 5)

### WeightToggles Component (Task 2)
- **WeightToggles.tsx** renders 4 checkboxes with student-friendly labels: "Easy Grades", "Great Teaching", "Low Difficulty", "Good Reviews"
- All 4 checkboxes ON by default (equal 25% weight each)
- **Last-toggle guard**: cannot uncheck the final enabled checkbox -- triggers shake animation (CSS keyframe, 0.4s)
- Unchecked labels use `text-muted-foreground` for visual de-emphasis
- Dynamic weight distribution text: "Each factor: X%" updates reactively
- 8 component tests covering rendering, toggle behavior, guard, and styling
- **CoursePage integration**: replaced WeightSliders with WeightToggles in both desktop sidebar and mobile Sheet
- Mobile Sheet button and title updated to "Customize Ranking"

### Cleanup
- Deleted `WeightSliders.tsx`, `WeightSliders.test.tsx`, and `slider.tsx` (no other consumers)

## Decisions Made

1. **Union type for backward compatibility**: `computeGauchoScore` accepts `Weights | ToggleWeights` with `typeof weights.gpa === 'boolean'` runtime check. This ensures any code still passing numeric weights continues to work.
2. **Kept old types intact**: `Weights`, `DEFAULT_WEIGHTS`, `normalizeWeights` remain exported -- no breaking changes.
3. **CSS keyframe for shake**: Plain CSS `@keyframes shake` with `.animate-shake` utility class, avoiding extra Tailwind plugin dependencies.
4. **Vertical checkbox stack**: Simpler layout than 2x2 grid, consistent with sidebar width constraints.

## Deviations from Plan

None -- plan executed exactly as written.

## Verification Results

- All 51 tests pass (9 test files)
- TypeScript `--noEmit` check passes with no errors
- Production build succeeds (vite build completes)
- Scoring tests: 17 pass (8 existing + 9 new)
- WeightToggles tests: 8 pass (all new)

## Self-Check: PASSED

- All created files exist on disk
- All deleted files confirmed removed
- Both task commits (d9c21ce, 2a29263) verified in git log

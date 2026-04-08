# Phase 10: Grade Distribution by Quarter - Context

**Gathered:** 2026-04-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace the all-time aggregate grade distribution chart with a quarter-aware view. Default to the most recent quarter's data, add a dropdown to select any specific quarter, and include an "All Quarters Combined" option. This is entirely a frontend change — the API already returns per-quarter grade data.

</domain>

<decisions>
## Implementation Decisions

### Quarter Selection UI
- Use shadcn/ui Select component for quarter dropdown — consistent with design system
- Default selection: "Most Recent" as the default option label — clearly distinct from quarter names
- "All Quarters Combined" is an additional option in the same dropdown — keeps controls unified
- Quarter labels use the format from the API: "Fall 2024", "Winter 2025", etc.

### Chart Behavior & Edge Cases
- Dynamic chart title above the bar chart: "Grade Distribution — Fall 2024" (or "— Most Recent" / "— All Quarters")
- When only 1 quarter exists: still show the dropdown with that quarter + "All Quarters Combined" (UI consistency)
- Dropdown lists quarters in reverse chronological order (most recent first)
- GPA trend line chart is NOT affected — it already shows per-quarter data correctly
- Only the grade distribution bar chart changes behavior

### Claude's Discretion
- Exact placement of the Select dropdown relative to the chart
- How "Most Recent" resolves to the actual most recent quarter in the data
- Whether to add the shadcn Select component via CLI or manually
- Test structure and mocking approach

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/src/components/GradeChart.tsx` — current bar chart component, receives `GradeQuarter[]`, sums all quarters
- `frontend/src/hooks/useProfessorGrades.ts` — fetches grades via React Query, returns `GradeQuarter[]`
- `frontend/src/types/api.ts` — `GradeQuarter` interface with `quarter: string` field (e.g., "Fall 2024")
- `frontend/src/components/GradeChart.test.tsx` — existing tests
- shadcn/ui Select component may need to be added

### Established Patterns
- Charts use Recharts (BarChart, ResponsiveContainer)
- Data fetching via React Query hooks
- Components receive typed props, tests use Vitest + RTL

### Integration Points
- `GradeChart.tsx` — needs new props for selected quarter + quarter list
- `ProfessorCard.tsx` — renders GradeChart, needs to manage quarter selection state
- No backend changes needed

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond the decisions above.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

# Phase 12: Design Tokens & Typography - Context

**Gathered:** 2026-04-09
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase)

<domain>
## Phase Boundary

Replace all CSS custom properties with Royal Blue + Snow White palette and swap Poppins/Open Sans for Inter. Establish the 4-size type scale. Update chart colors to blue-family. Ensure score badge colors meet 4.5:1 contrast on white cards. No new components, no layout changes — purely token replacement and font swap.

</domain>

<decisions>
## Implementation Decisions

### Color Palette (Locked from milestone definition)
- Primary: #2563EB (Royal Blue)
- Secondary: #93C5FD (Sky Blue)
- Background: #FAFBFF (Snow with blue hint)
- Card: #FFFFFF (White)
- Text: #111827 (Near black)
- Accent: #DBEAFE (Light blue wash)
- CTA buttons: #2563EB with white text
- Muted: #F1F5F9 (Slate 100)
- Muted foreground: #64748B (Slate 500)
- Border: #E2E8F0 (Slate 200)

### Typography (Locked)
- Font: Inter (single family for all text)
- Install via @fontsource-variable/inter
- Remove @fontsource/poppins and @fontsource-variable/open-sans
- Type scale: 14px (label), 16px (body), 20px (heading), 28px (display)

### Chart Colors (Blue family)
- Chart 1: #2563EB (primary blue)
- Chart 2: #3B82F6 (medium blue)
- Chart 3: #60A5FA (light blue)
- Chart 4: #93C5FD (sky blue)
- Chart 5: #1E40AF (dark blue)

### Score Badge Colors (Preserved semantics, updated for contrast)
- >= 70: #16A34A (green-600) on white — 4.5:1 ✓
- 50-69: #CA8A04 (yellow-600) on white — 4.5:1 ✓
- < 50: #DC2626 (red-600) on white — 4.5:1 ✓

### Claude's Discretion
- Exact oklch conversions for all hex values
- Ring, input, destructive token values
- Dark mode token block (update to non-achromatic blue-tinted values if time permits)

</decisions>

<code_context>
## Existing Code Insights

### Files to Modify
- `frontend/src/index.css` — all :root CSS variables, font imports, @theme inline block
- `frontend/package.json` — swap font dependencies
- `frontend/src/components/GradeChart.tsx` — hardcoded #0F766E bar fill
- `frontend/src/components/GpaTrendChart.tsx` — hardcoded #0D9488 line stroke
- `frontend/src/components/ProfessorCard.tsx` — score badge color classes (bg-green-500 etc.)

### Integration Points
- Every component that uses `bg-primary`, `text-primary`, `bg-accent` will automatically inherit new colors
- Font change propagates via `--font-sans` and `--font-heading` tokens
- Chart colors need direct update (hardcoded hex, not tokens)

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond the locked decisions.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>

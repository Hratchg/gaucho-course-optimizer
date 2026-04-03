# Phase 5: Branding & Design System - Context

**Gathered:** 2026-04-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Apply the Deep Teal + Amber visual identity globally across all existing pages and components. Replace shadcn/ui's default gray/neutral CSS tokens with the brand palette, swap Geist Variable for a Poppins + Open Sans font pairing, add a favicon and OG meta tags. No new pages, no new features, no backend changes — purely visual token replacement and meta tag additions.

</domain>

<decisions>
## Implementation Decisions

### Color System
- **D-01:** Replace all `:root` CSS variable values in `src/index.css` with the Deep Teal + Amber palette. Primary: #0F766E (deep teal), Secondary: #0D9488 (medium teal), Accent: #D97706 (rich amber), Background: #F0FDFA (soft teal tint), Text: #134E4A (dark teal). Convert hex values to oklch format to match existing shadcn/ui token format.
- **D-02:** Gaucho Score color banding stays traffic-light: green (>=70), yellow (50-69), red (<50). These are NOT replaced by brand colors — universal recognition takes priority.
- **D-03:** Gaucho Score displayed as a **colored badge/pill** (rounded, colored background with white text) on professor cards. Replaces whatever the current implementation is (border, text color, etc.).

### Typography
- **D-04:** Heading font: **Poppins** (weights 400, 500, 600, 700) via Google Fonts or @fontsource.
- **D-05:** Body font: **Open Sans** (weights 300, 400, 500, 600, 700) via Google Fonts or @fontsource.
- **D-06:** Remove `@fontsource-variable/geist` import and replace `--font-sans` / `--font-heading` CSS variables with the new fonts.

### Charts & Data Colors
- **D-07:** Claude's discretion on Recharts chart colors. Balance brand cohesion (teal palette) with data clarity. Grade distribution bars and GPA trend lines should look intentional, not default gray.

### Favicon & Meta
- **D-08:** Favicon: text-based "GCO" monogram (or "G" at small sizes) in Deep Teal on white background. Generate as SVG favicon + PNG fallbacks (32x32, 16x16).
- **D-09:** OG image (1200x630): Deep Teal background, white text "Gaucho Course Optimizer", tagline "Find the best professor for any UCSB course.", amber accent element.
- **D-10:** Page titles use per-page format: `[Page/Course Name] | Gaucho Course Optimizer`. Examples: "Search | Gaucho Course Optimizer", "CMPSC 130A | Gaucho Course Optimizer".

### Claude's Discretion
- Chart color palette — pick the approach that best balances brand identity with data readability
- Page title format — decided: per-page titles with `| Gaucho Course Optimizer` suffix
- Exact oklch conversions for the hex palette
- Font loading strategy (Google Fonts CDN vs @fontsource packages)
- OG image generation approach (static asset vs programmatic)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Styling
- `frontend/src/index.css` — Current CSS variable definitions (oklch format), Tailwind v4 `@theme inline` block, Geist font import. This is the primary file to modify.
- `frontend/src/components/ui/*.tsx` — shadcn/ui primitives that consume theme tokens. Should not need modification if tokens are correctly replaced.

### Components to Update
- `frontend/src/components/ProfessorCard.tsx` — Gaucho Score display needs colored badge/pill treatment (D-03)
- `frontend/src/components/GradeChart.tsx` — Grade distribution bar chart colors (D-07)
- `frontend/src/components/GpaTrendChart.tsx` — GPA trend line color (D-07)

### Phase Requirements
- `.planning/REQUIREMENTS.md` §Branding & Theming — BRAND-01, BRAND-02, BRAND-03

### Prior Phase Context
- `.planning/phases/03-react-frontend/03-CONTEXT.md` — Phase 3 decisions on card layout, chart setup, color banding thresholds

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/src/components/ui/badge.tsx` — shadcn/ui Badge component. Can be used for the Gaucho Score colored badge (D-03).
- `frontend/src/components/ui/card.tsx` — Card component already consumes `--card`, `--card-foreground` tokens. Will inherit new colors automatically.

### Established Patterns
- **CSS Variables:** All colors defined as oklch values in `:root` in `src/index.css`. shadcn/ui components reference via `var(--primary)`, `var(--accent)`, etc. Token replacement propagates automatically.
- **Tailwind v4:** Uses `@theme inline` block to map CSS variables to Tailwind utility classes. No `tailwind.config.js` — configuration is CSS-first.
- **Font loading:** Currently `@import "@fontsource-variable/geist"` in `src/index.css`. Same pattern works for Poppins/Open Sans via @fontsource packages.

### Integration Points
- `frontend/index.html` — Favicon link tags, OG meta tags, and page title go here
- `frontend/src/App.tsx` — Current routes: `/` (SearchPage), `/courses/:courseId` (CoursePage). Per-page title updates need a mechanism (react-helmet-async or manual `document.title`).
- `frontend/src/pages/SearchPage.tsx` and `frontend/src/pages/CoursePage.tsx` — Will need per-page title setting.

</code_context>

<specifics>
## Specific Ideas

- Design system palette confirmed via ui-ux-pro-max research: Deep Teal (#0F766E) primary, Medium Teal (#0D9488) secondary, Rich Amber (#D97706) accent, Soft Teal Tint (#F0FDFA) background, Dark Teal (#134E4A) text foreground.
- Typography confirmed: Poppins (geometric, rounded) for headings, Open Sans (humanist, readable) for body.
- Border, muted, and card token values should follow the palette — e.g., border in a light teal like #99F6E4 or a muted #E8F0F3.
- Favicon is text-based ("GCO" / "G") — no external design assets needed.
- OG image should be a static asset (simplest approach, no build-time generation).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 05-branding-design-system*
*Context gathered: 2026-04-02*

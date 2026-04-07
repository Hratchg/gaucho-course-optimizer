# Phase 7: Tutorial Landing Page - Context

**Gathered:** 2026-04-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace the placeholder HomePage with a full tutorial landing page. The page explains how Gaucho Score works, defines all four scoring factors with examples, provides a step-by-step usage guide, and has prominent CTAs to begin searching. No new routes, no backend changes, no new dependencies — purely content and layout work on the existing HomePage.tsx.

</domain>

<decisions>
## Implementation Decisions

### Gaucho Score Visual Breakdown
- Horizontal stacked bar showing 4 weighted segments (GPA, Quality, Difficulty, Sentiment) summing to 100 — pure CSS, no chart library needed
- Display "25% each by default" with a note that weights are adjustable on the results page
- Each factor gets a distinct teal shade from the brand palette — visually differentiates while staying on-brand
- Static diagram — Phase 8 introduces toggle controls, this is just explanation

### Factor Definitions & Usage Guide
- 2x2 card grid for factor definitions — each card has factor icon (from lucide-react), name, one-line definition, and a real example value
- Use realistic example numbers: "GPA: 3.45/4.00", "Quality: 4.2/5.0", "Difficulty: 2.8/5.0", "Sentiment: 72%"
- 3-step usage guide: (1) Search a course, (2) Compare professors, (3) Adjust your priorities — with icons
- Steps visualized as numbered circles with connecting lines — left-to-right on desktop, top-to-bottom on mobile

### Page Structure & CTA Placement
- Section order: Hero → Score Breakdown → Factor Cards → Usage Guide → Final CTA
- Final CTA: full-width banner section with "Ready to find your professor?" heading + prominent accent button
- Generous vertical padding (64px between sections) — tutorial content should breathe
- Natural scroll — no sticky elements beyond navbar, no parallax or animations

### Claude's Discretion
- Exact wording for factor definitions (keep it jargon-free, student-friendly)
- Icon selection for each factor and step (use lucide-react)
- Teal shade distribution across the 4 factor segments
- Responsive breakpoint behavior for the 2x2 grid (stack on mobile)
- Exact hero heading and subheading copy

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/src/pages/HomePage.tsx` — placeholder from Phase 6, will be replaced entirely
- `frontend/src/components/ui/card.tsx` — shadcn Card component for factor definition cards
- `frontend/src/components/ui/button.tsx` — shadcn Button for CTA
- `lucide-react` icons available (GraduationCap, Star, TrendingDown, MessageCircle, Search, etc.)
- Brand tokens in `frontend/src/index.css` — Deep Teal primary, Amber accent

### Established Patterns
- Pages in `frontend/src/pages/`, components in `frontend/src/components/`
- Tailwind v4 with `@theme inline` tokens
- `useEffect` for document.title
- Tests with Vitest + React Testing Library

### Integration Points
- `frontend/src/pages/HomePage.tsx` — direct replacement of placeholder content
- Links to `/search` via React Router `Link`
- No other files need modification (routing is already set up from Phase 6)

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond the decisions above.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

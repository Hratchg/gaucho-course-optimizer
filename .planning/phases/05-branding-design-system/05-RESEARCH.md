# Phase 5: Branding & Design System - Research

**Researched:** 2026-04-02
**Domain:** CSS design tokens (Tailwind v4 / shadcn/ui), @fontsource typography, SVG favicon, OG meta tags, per-page titles
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Replace all `:root` CSS variable values in `src/index.css` with the Deep Teal + Amber palette. Primary: #0F766E (deep teal), Secondary: #0D9488 (medium teal), Accent: #D97706 (rich amber), Background: #F0FDFA (soft teal tint), Text: #134E4A (dark teal). Convert hex values to oklch format to match existing shadcn/ui token format.
- **D-02:** Gaucho Score color banding stays traffic-light: green (>=70), yellow (50-69), red (<50). NOT replaced by brand colors — universal recognition takes priority.
- **D-03:** Gaucho Score displayed as a **colored badge/pill** (rounded, colored background with white text) on professor cards. Replaces current border-left colored card approach.
- **D-04:** Heading font: **Poppins** (weights 400, 500, 600, 700) via @fontsource.
- **D-05:** Body font: **Open Sans** (weights 300, 400, 500, 600, 700) via @fontsource.
- **D-06:** Remove `@fontsource-variable/geist` import and replace `--font-sans` / `--font-heading` CSS variables with the new fonts.
- **D-07:** Claude's discretion on Recharts chart colors. Balance brand cohesion (teal palette) with data clarity.
- **D-08:** Favicon: text-based "GCO" monogram (or "G" at small sizes) in Deep Teal on white background. Generate as SVG favicon + PNG fallbacks (32x32, 16x16).
- **D-09:** OG image (1200x630): Deep Teal background, white text "Gaucho Course Optimizer", tagline "Find the best professor for any UCSB course.", amber accent element.
- **D-10:** Page titles use per-page format: `[Page/Course Name] | Gaucho Course Optimizer`. Examples: "Search | Gaucho Course Optimizer", "CMPSC 130A | Gaucho Course Optimizer".

### Claude's Discretion

- Chart color palette — pick the approach that best balances brand identity with data readability
- Exact oklch conversions for the hex palette
- Font loading strategy (Google Fonts CDN vs @fontsource packages)
- OG image generation approach (static asset vs programmatic)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BRAND-01 | User sees a cohesive Deep Teal (#0F766E) + Amber (#D97706) color scheme across all pages and components | CSS variable replacement in `index.css` `:root` block propagates automatically to all shadcn/ui components via `@theme inline` mapping |
| BRAND-02 | User sees professional typography with a distinct heading and body font pairing | `@fontsource-variable/poppins` + `@fontsource-variable/open-sans` replace Geist; `--font-heading` and `--font-sans` CSS variables updated |
| BRAND-03 | User sees a custom favicon, descriptive page titles, and Open Graph meta tags when sharing links | SVG favicon in `public/`, `index.html` updated with OG tags; `document.title` set per-page in SearchPage and CoursePage |
</phase_requirements>

---

## Summary

Phase 5 is a pure visual token replacement and meta-tag phase — no new pages, no backend changes, no new routing. All work falls into four buckets: (1) CSS variable replacement in `index.css`, (2) font swap, (3) Gaucho Score badge refactor in `ProfessorCard.tsx`, and (4) favicon + OG meta in `index.html` with per-page titles.

The existing architecture is well-suited for this work. Tailwind v4's `@theme inline` block already maps `:root` CSS variables to utility classes, meaning a single edit to the `:root` block in `index.css` propagates brand colors to every shadcn/ui component automatically — `Card`, `Badge`, `Button`, `Sheet`, `Collapsible` all inherit without modification. The chart color updates (`GradeChart.tsx` and `GpaTrendChart.tsx`) require only a hardcoded hex string change in two files. The Gaucho Score display refactor in `ProfessorCard.tsx` is the most significant component change: the current `border-left` approach must be replaced with a `<Badge>` or inline-styled `<span>` using the traffic-light palette.

For page titles, the simplest correct approach for this project (client-side SPA, no SSR) is direct `document.title` assignment in a `useEffect` hook in each page component. This avoids adding `react-helmet-async` as a new dependency for a two-page app. The static OG image should be placed in `public/` and referenced from `index.html` as an absolute URL.

**Primary recommendation:** Edit `index.css` `:root` block with oklch-converted brand tokens, swap fonts via `@fontsource-variable` packages, refactor score badge in `ProfessorCard.tsx`, and update `index.html` for favicon + OG + base title.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `@fontsource-variable/poppins` | 5.2.7 | Self-hosted Poppins variable font | Same import pattern as existing Geist; no CDN dependency; works with Vite |
| `@fontsource-variable/open-sans` | 5.2.7 | Self-hosted Open Sans variable font | Same pattern; covers weights 300–700 in single file |
| CSS custom properties (`:root`) | built-in | Design token source of truth | Already used by shadcn/ui; Tailwind v4 `@theme inline` maps them to utilities |
| SVG + PNG favicon | browser built-in | Multi-format favicon strategy | SVG for modern browsers; PNG fallback for Safari < 15.6 |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `react-helmet-async` | 3.0.0 (available on npm) | Per-page `<title>` and `<meta>` management | NOT needed here — `document.title` assignment in `useEffect` is sufficient for this 2-page SPA with no SSR |
| Recharts `fill`/`stroke` prop | built-in (recharts 3.8.1) | Chart series coloring | Pass brand hex strings directly to `<Bar fill>` and `<Line stroke>` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `@fontsource-variable/poppins` | Google Fonts CDN `<link>` | CDN is faster to set up but adds external dependency, GDPR concern, and FOUT risk; @fontsource is self-hosted and matches existing project pattern |
| `document.title` in `useEffect` | `react-helmet-async` | Helmet is needed for SSR or complex multi-level head management; `document.title` is sufficient and avoids a new dependency for this phase |
| Static PNG favicon | Emoji/SVG-only favicon | PNG fallback required for Safari support; SVG primary with PNG fallback covers 100% of browsers |

**Installation (new packages only):**
```bash
npm install @fontsource-variable/poppins @fontsource-variable/open-sans
```

**Version verification (confirmed 2026-04-02):**
```bash
npm view @fontsource-variable/poppins version  # 5.2.7
npm view @fontsource-variable/open-sans version # 5.2.7
```

---

## Architecture Patterns

### Files Modified in This Phase

```
frontend/
├── src/
│   ├── index.css                        # Token replacement + font import swap
│   ├── components/
│   │   ├── ProfessorCard.tsx            # Score badge refactor (D-03)
│   │   ├── GradeChart.tsx               # Bar fill color (D-07)
│   │   └── GpaTrendChart.tsx            # Line stroke color (D-07)
│   └── pages/
│       ├── SearchPage.tsx               # document.title (D-10)
│       └── CoursePage.tsx               # document.title (D-10)
└── index.html                           # Favicon links, OG meta tags (D-08, D-09)
public/
├── favicon.svg                          # SVG monogram favicon (D-08)
├── favicon-32x32.png                    # PNG fallback (D-08)
├── favicon-16x16.png                    # PNG fallback (D-08)
└── og-image.png                         # OG share image 1200x630 (D-09)
```

### Pattern 1: CSS Token Replacement (`:root` block)

**What:** Replace all `:root` oklch values in `src/index.css` with brand palette values. The `@theme inline` block above `:root` already maps tokens to Tailwind utilities — no changes needed there.

**When to use:** Single edit propagates to all shadcn/ui components automatically.

**Verified oklch conversions (computed 2026-04-02 using OKLCH color math):**

```css
/* Source: OKLCH color math (IEC 61966-2-1, Oklab spec) */
:root {
  --background: oklch(0.9836 0.0142 180.72);   /* #F0FDFA soft teal tint */
  --foreground: oklch(0.3861 0.0590 188.42);   /* #134E4A dark teal text */
  --card: oklch(1.0000 0.0000 0);              /* #FFFFFF white card surface */
  --card-foreground: oklch(0.3861 0.0590 188.42); /* #134E4A */
  --popover: oklch(1.0000 0.0000 0);           /* #FFFFFF */
  --popover-foreground: oklch(0.3861 0.0590 188.42); /* #134E4A */
  --primary: oklch(0.5109 0.0861 186.39);      /* #0F766E deep teal */
  --primary-foreground: oklch(1.0000 0.0000 0); /* #FFFFFF white */
  --secondary: oklch(0.6002 0.1038 184.70);    /* #0D9488 medium teal */
  --secondary-foreground: oklch(1.0000 0.0000 0); /* #FFFFFF white */
  --muted: oklch(0.9751 0.0096 189.07);        /* #F0F9F8 very light teal */
  --muted-foreground: oklch(0.6112 0.0366 186.82); /* #6B8B87 muted teal gray */
  --accent: oklch(0.6658 0.1574 58.32);        /* #D97706 rich amber */
  --accent-foreground: oklch(1.0000 0.0000 0); /* #FFFFFF white */
  --destructive: oklch(0.577 0.245 27.325);    /* keep existing red */
  --border: oklch(0.9100 0.0927 180.43);       /* #99F6E4 light teal border */
  --input: oklch(0.9100 0.0927 180.43);        /* #99F6E4 */
  --ring: oklch(0.8549 0.1251 181.07);         /* #5EEAD4 teal-300 focus ring */
  --chart-1: oklch(0.5109 0.0861 186.39);      /* primary teal */
  --chart-2: oklch(0.6658 0.1574 58.32);       /* amber */
  --chart-3: oklch(0.6002 0.1038 184.70);      /* secondary teal */
  --chart-4: oklch(0.7500 0.1000 180.00);      /* lighter teal */
  --chart-5: oklch(0.3861 0.0590 188.42);      /* dark teal */
  --radius: 0.625rem;
  /* sidebar tokens: update to match brand */
  --sidebar: oklch(0.9751 0.0096 189.07);
  --sidebar-foreground: oklch(0.3861 0.0590 188.42);
  --sidebar-primary: oklch(0.5109 0.0861 186.39);
  --sidebar-primary-foreground: oklch(1.0000 0.0000 0);
  --sidebar-accent: oklch(0.9100 0.0927 180.43);
  --sidebar-accent-foreground: oklch(0.3861 0.0590 188.42);
  --sidebar-border: oklch(0.9100 0.0927 180.43);
  --sidebar-ring: oklch(0.8549 0.1251 181.07);
}
```

> Note: The `.dark` block is out of scope (dark mode excluded from v1.1). Leave it as-is or remove entirely — no dark mode toggle exists in the app.

### Pattern 2: Font Import Swap

**What:** Remove `@fontsource-variable/geist` import; add `@fontsource-variable/poppins` and `@fontsource-variable/open-sans`; update CSS variable assignments in `@theme inline`.

```css
/* Source: @fontsource documentation — https://fontsource.org/fonts/poppins/install */

/* Remove this line: */
/* @import "@fontsource-variable/geist"; */

/* Add these: */
@import "@fontsource-variable/poppins";
@import "@fontsource-variable/open-sans";

/* In @theme inline block, update: */
@theme inline {
  --font-heading: 'Poppins Variable', sans-serif;
  --font-sans: 'Open Sans Variable', sans-serif;
  /* ... rest unchanged ... */
}
```

**Font name strings for variable fonts:**
- `@fontsource-variable/poppins` → font-family: `'Poppins Variable'`
- `@fontsource-variable/open-sans` → font-family: `'Open Sans Variable'`

These names are set by the @fontsource package's bundled CSS — verify with `node_modules/@fontsource-variable/poppins/index.css` after install.

### Pattern 3: Gaucho Score Badge Refactor

**What:** Replace `scoreBorderClass()` border-left approach in `ProfessorCard.tsx` with an inline-styled score badge using `<Badge>` (shadcn/ui) with className overrides for traffic-light colors.

**Current (to remove):**
```tsx
// Current approach — border only, score displayed as plain number
function scoreBorderClass(score: number): string {
  if (score >= 70) return 'border-l-4 border-l-green-500'
  if (score >= 50) return 'border-l-4 border-l-yellow-500'
  return 'border-l-4 border-l-red-500'
}
// Used as: <Card className={`${scoreBorderClass(score)} mb-6`}>
// Score shown as: <span className="text-[28px] font-semibold leading-none">{score}</span>
```

**New approach:**
```tsx
// Badge/pill with traffic-light color banding (D-02 + D-03)
function scoreColorClass(score: number): string {
  if (score >= 70) return 'bg-green-500 text-white'
  if (score >= 50) return 'bg-yellow-500 text-white'
  return 'bg-red-500 text-white'
}

// In render:
<Badge className={`${scoreColorClass(score)} text-sm font-bold px-2.5 py-1`}>
  {score}
</Badge>

// Card no longer needs border class:
<Card className="mb-6">
```

The `Badge` component accepts `className` override via `cn()` — existing variants do not need modification.

### Pattern 4: Per-Page Titles with `document.title`

**What:** Set `document.title` via `useEffect` in each page component.

```tsx
// Source: MDN Web Docs — document.title
// In SearchPage.tsx:
import { useEffect } from 'react'

export default function SearchPage() {
  useEffect(() => {
    document.title = 'Search | Gaucho Course Optimizer'
  }, [])
  // ...
}

// In CoursePage.tsx — dynamic based on courseId:
export default function CoursePage() {
  const { courseId } = useParams<{ courseId: string }>()
  useEffect(() => {
    // courseId is like "CMPSC-130A" from URL — format for display
    const displayId = courseId?.replace('-', ' ') ?? 'Course'
    document.title = `${displayId} | Gaucho Course Optimizer`
  }, [courseId])
  // ...
}
```

**Note:** The `courseId` URL param format should be inspected in the existing data — currently it is a numeric ID (e.g., `/courses/123`). The display title may need to use the course name from fetched professor data rather than the raw param. Check `useProfessors` hook return type.

### Pattern 5: Favicon HTML in `index.html`

```html
<!-- Source: web.dev adaptive favicon guide -->
<head>
  <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
  <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
  <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png" />
  <link rel="apple-touch-icon" sizes="180x180" href="/favicon-32x32.png" />

  <!-- Open Graph -->
  <meta property="og:title" content="Gaucho Course Optimizer" />
  <meta property="og:description" content="Find the best professor for any UCSB course." />
  <meta property="og:image" content="https://gaucho-course-optimizer.vercel.app/og-image.png" />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="https://gaucho-course-optimizer.vercel.app" />

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="Gaucho Course Optimizer" />
  <meta name="twitter:description" content="Find the best professor for any UCSB course." />
  <meta name="twitter:image" content="https://gaucho-course-optimizer.vercel.app/og-image.png" />

  <title>Gaucho Course Optimizer</title>
</head>
```

**OG image absolute URL:** Must be a full URL (not relative path). Use the deployed Vercel domain. The `og:image` value set in `index.html` serves as the default; per-page OG metadata would require `react-helmet-async` (out of scope for this phase).

### Pattern 6: SVG Favicon Markup

```svg
<!-- public/favicon.svg — inline SVG text monogram -->
<!-- Source: web.dev SVG favicon guide -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="4" fill="#ffffff"/>
  <text
    x="16" y="22"
    font-family="sans-serif"
    font-size="14"
    font-weight="700"
    fill="#0F766E"
    text-anchor="middle"
  >GCO</text>
</svg>
```

For PNG fallback generation: use any SVG-to-PNG tool (Inkscape CLI, sharp npm package, or online converter). The implementer can use `sharp` as a one-time dev script or generate manually.

### Anti-Patterns to Avoid

- **Editing `@theme inline` color mappings:** The `--color-primary: var(--primary)` mappings in `@theme inline` do NOT need to change — they reference `:root` variables by name. Only `:root` values change.
- **Adding `!important` to override tokens:** Token replacement in `:root` is sufficient; no component-level overrides should be needed.
- **Relative path for `og:image`:** Social crawlers fetch OG images from an absolute URL. `/og-image.png` will fail on most platforms.
- **Forgetting `.dark` block side effects:** The `.dark` block in `index.css` still references old gray tokens. Since dark mode is excluded from v1.1, this is acceptable — but leaving inconsistent dark values could cause visible issues if dark mode is ever accidentally triggered. Consider leaving `.dark` block as-is or removing it.
- **Using `@fontsource/poppins` (non-variable) when `@fontsource-variable/poppins` exists:** The variable version covers all weights (100–900) in a single file; the non-variable version requires one import per weight.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CSS token generation | Custom sass/js palette generator | Direct `:root` CSS variable editing | Tailwind v4 + shadcn/ui already has the token architecture; just replace values |
| Font loading | `@font-face` declarations from scratch | `@fontsource-variable/*` packages | Fontsource handles `@font-face`, woff2 format, subsetting, weight ranges |
| Page titles | `react-helmet-async` | `document.title` in `useEffect` | No SSR means Helmet's server-rendering value is irrelevant; `document.title` is direct DOM |
| OG image generation | `@vercel/og`, canvas API, puppeteer | Static PNG asset in `public/` | The simplest approach that works; no build pipeline changes required |
| Score badge colors | Custom CSS classes | Tailwind utility classes + `<Badge className>` | `Badge` already accepts className override; Tailwind green/yellow/red utilities are correct for traffic-light |

**Key insight:** This phase is almost entirely configuration and token replacement — every meaningful problem is already solved by the existing libraries. The only real implementation work is the score badge refactor and generating the two static image assets (favicon PNG, OG image).

---

## Common Pitfalls

### Pitfall 1: oklch Value Accuracy

**What goes wrong:** Incorrect oklch conversions produce slightly wrong brand colors — e.g., a muddy teal instead of clean #0F766E.
**Why it happens:** Online oklch converters sometimes use different white point assumptions or truncate values.
**How to avoid:** Use the verified conversions in the Pattern 1 table above (computed using IEC 61966-2-1 linearization + Oklab matrix). Cross-check with `oklch.com` interactive picker.
**Warning signs:** The rendered color looks visually different from the hex source color when compared side-by-side.

### Pitfall 2: `@fontsource-variable` Font Family Name String

**What goes wrong:** After installing `@fontsource-variable/poppins`, using `font-family: 'Poppins'` (not `'Poppins Variable'`) fails to apply the variable font — browser falls back to system sans-serif.
**Why it happens:** The variable fontsource package registers the font-family as `'Poppins Variable'` in its bundled CSS, distinct from the static weight packages.
**How to avoid:** After installing, inspect `node_modules/@fontsource-variable/poppins/index.css` for the exact `font-family` string. The pattern is always `'{Name} Variable'`.
**Warning signs:** Font metrics look different from expected, or devtools shows "system-ui" fallback.

### Pitfall 3: OG `meta` Tags Must Precede `<title>` in `<head>`

**What goes wrong:** Some social crawlers (particularly LinkedIn) stop parsing `<head>` once they hit a `<script type="module">` tag. OG tags placed after the script tag may not be read.
**Why it happens:** Vite's `index.html` puts the module script in `<head>`. If OG tags come after it, they may be missed.
**How to avoid:** Place all `<meta property="og:*">` tags before the `<script type="module">` line. The current `index.html` only has `<script>` in `<body>`, so this is not currently an issue — but verify placement.
**Warning signs:** Facebook/LinkedIn share preview shows no title or image.

### Pitfall 4: Gaucho Score Test Breakage

**What goes wrong:** `ProfessorCard.test.tsx` currently asserts that the score value `75` appears in the DOM as plain text (`screen.getByText('75')`). After wrapping the score in `<Badge>`, the assertion still works — but if the Badge renders differently in happy-dom, it may fail.
**Why it happens:** `<Badge>` renders as a `<span>` element with className. `getByText('75')` should still find it. However, if className overrides cause happy-dom rendering issues, the test may need updating.
**How to avoid:** Run `npm test` after the badge refactor. If `getByText('75')` fails, update to `screen.getByRole('status')` with aria-label or use `screen.getByText('75', { selector: 'span' })`.
**Warning signs:** Test failure: "Unable to find an element with the text: 75".

### Pitfall 5: `document.title` Reset on Navigation

**What goes wrong:** In a React SPA, navigating between pages does not reset `document.title` unless each page sets it. If the user navigates from CoursePage back to SearchPage without the SearchPage `useEffect` running again (e.g., component already mounted), the title may be stale.
**Why it happens:** React Router re-renders the component on navigation, which re-triggers `useEffect` with an empty dependency array — so this should work correctly. But if the page is cached in React Router and not remounted, it may not.
**How to avoid:** Test navigation in-browser after implementation. Title should update on every navigation.
**Warning signs:** Browser tab still shows "CMPSC 130A | Gaucho Course Optimizer" after navigating back to Search.

### Pitfall 6: CoursePage Title Needs Course Name, Not Numeric ID

**What goes wrong:** `CoursePage` receives `courseId` as a **numeric** URL param (e.g., `/courses/123`). Setting `document.title = '123 | Gaucho Course Optimizer'` is uninformative.
**Why it happens:** The URL param is a database ID, not the display name.
**How to avoid:** Set the title from the fetched professor data — professors have a course name context. Alternatively, check if the existing `useProfessors` hook returns course name metadata. If not, use a fallback like "Course Results | Gaucho Course Optimizer" initially and update to the real name when data loads.
**Warning signs:** Browser tab shows a number instead of a course name.

---

## Code Examples

### Full Updated `:root` Block

```css
/* Source: computed oklch values (2026-04-02) + shadcn/ui token schema */
:root {
  --background: oklch(0.9836 0.0142 180.72);
  --foreground: oklch(0.3861 0.0590 188.42);
  --card: oklch(1.0000 0.0000 0);
  --card-foreground: oklch(0.3861 0.0590 188.42);
  --popover: oklch(1.0000 0.0000 0);
  --popover-foreground: oklch(0.3861 0.0590 188.42);
  --primary: oklch(0.5109 0.0861 186.39);
  --primary-foreground: oklch(1.0000 0.0000 0);
  --secondary: oklch(0.6002 0.1038 184.70);
  --secondary-foreground: oklch(1.0000 0.0000 0);
  --muted: oklch(0.9751 0.0096 189.07);
  --muted-foreground: oklch(0.6112 0.0366 186.82);
  --accent: oklch(0.6658 0.1574 58.32);
  --accent-foreground: oklch(1.0000 0.0000 0);
  --destructive: oklch(0.577 0.245 27.325);
  --border: oklch(0.9100 0.0927 180.43);
  --input: oklch(0.9100 0.0927 180.43);
  --ring: oklch(0.8549 0.1251 181.07);
  --chart-1: oklch(0.5109 0.0861 186.39);
  --chart-2: oklch(0.6658 0.1574 58.32);
  --chart-3: oklch(0.6002 0.1038 184.70);
  --chart-4: oklch(0.7500 0.1000 180.00);
  --chart-5: oklch(0.3861 0.0590 188.42);
  --radius: 0.625rem;
  --sidebar: oklch(0.9751 0.0096 189.07);
  --sidebar-foreground: oklch(0.3861 0.0590 188.42);
  --sidebar-primary: oklch(0.5109 0.0861 186.39);
  --sidebar-primary-foreground: oklch(1.0000 0.0000 0);
  --sidebar-accent: oklch(0.9100 0.0927 180.43);
  --sidebar-accent-foreground: oklch(0.3861 0.0590 188.42);
  --sidebar-border: oklch(0.9100 0.0927 180.43);
  --sidebar-ring: oklch(0.8549 0.1251 181.07);
}
```

### Font Import Section (top of `index.css`)

```css
/* Source: fontsource.org — @fontsource-variable pattern */
@import "tailwindcss";
@import "tw-animate-css";
@import "shadcn/tailwind.css";
@import "@fontsource-variable/poppins";
@import "@fontsource-variable/open-sans";
/* Remove: @import "@fontsource-variable/geist"; */
```

### Chart Colors (Recharts — brand teal + amber)

```tsx
/* GradeChart.tsx — replace fill="#6366f1" */
<Bar dataKey="count" fill="#0F766E" />

/* GpaTrendChart.tsx — replace stroke="#10b981" */
<Line type="monotone" dataKey="avg_gpa" stroke="#0D9488" dot={false} />
```

Rationale: Primary teal (#0F766E) for grade bars (brand cohesion), secondary teal (#0D9488) for GPA trend line (slightly differentiated). Both are recognizable data series colors distinct from background.

### Score Badge in ProfessorCard

```tsx
/* Source: shadcn/ui Badge component + Tailwind utility overrides */
function scoreColorClass(score: number): string {
  if (score >= 70) return 'bg-green-500 text-white hover:bg-green-500'
  if (score >= 50) return 'bg-yellow-500 text-white hover:bg-yellow-500'
  return 'bg-red-500 text-white hover:bg-red-500'
}

// Replace the <span> score display with:
<Badge className={`${scoreColorClass(score)} text-sm font-bold px-2.5 py-1 rounded-full`}>
  {score}
</Badge>

// Remove scoreBorderClass and its usage from <Card className>
// <Card className="mb-6"> (no border class)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Google Fonts `<link>` CDN | `@fontsource-variable/*` npm packages | ~2021 (Fontsource v4) | Self-hosted, tree-shakeable, no CDN latency |
| HSL CSS variables | OKLCH CSS variables | shadcn/ui v2 / Tailwind v4 (2024) | Perceptually uniform color space; better color interpolation |
| `tailwind.config.js` extend.colors | `@theme inline` CSS-first config | Tailwind v4 (2025) | No JS config; CSS variables are the single source of truth |
| `react-helmet` | `react-helmet-async` | ~2020 | Thread-safe; async SSR support |

**Deprecated/outdated:**
- `tailwind.config.js` color extension: Tailwind v4 uses `@theme inline`; no `tailwind.config.js` exists in this project
- `@fontsource/poppins` (non-variable): Replaced by `@fontsource-variable/poppins` which covers all weights in one import
- `<link rel="shortcut icon" href="/favicon.ico">`: `rel="icon"` is the modern standard; `shortcut` prefix is deprecated but harmless

---

## Open Questions

1. **CoursePage: course display name for title**
   - What we know: `courseId` URL param is numeric (e.g., `123`); `useProfessors` hook fetches professor data
   - What's unclear: Does the API return a course name alongside professor data? If not, "Course Results | Gaucho Course Optimizer" is the fallback.
   - Recommendation: Inspect the `ProfessorRanking` type in `frontend/src/types/api.ts` and the API response for a course name field. If available, use it in the title. If not, use generic fallback for Phase 5 and note as a future improvement.

2. **OG image production asset**
   - What we know: Static PNG at 1200x630 is the simplest approach (D-09 decision)
   - What's unclear: How the implementer creates the PNG — no design tool is specified
   - Recommendation: The planner should include a task for generating the OG PNG. Options: (a) create as SVG then rasterize with `sharp` or Inkscape, (b) use Figma/Canva export, (c) create programmatically with `node-canvas` or similar. All produce a valid static asset.

3. **`.dark` block disposition**
   - What we know: Dark mode is out of scope for v1.1
   - What's unclear: Whether leaving the old gray `.dark` values causes any visual artifact (dark mode media query or class)
   - Recommendation: The app has no dark mode toggle and no `prefers-color-scheme` media query check. The `.dark` class would only activate if someone manually adds `class="dark"` to `<html>`. It is safe to leave the `.dark` block as-is. No action required.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | npm install | ✓ | v20.9.0 | — |
| npm | Package install | ✓ | 10.1.0 | — |
| `@fontsource-variable/poppins` | Font swap | install needed | 5.2.7 (on npm) | Google Fonts CDN |
| `@fontsource-variable/open-sans` | Font swap | install needed | 5.2.7 (on npm) | Google Fonts CDN |
| PNG generation tool | Favicon + OG image | ✗ (none detected) | — | Create SVG + convert manually; or use sharp as dev script |
| Browser (any modern) | Visual verification | assumed | — | — |

**Missing dependencies with no fallback:**
- PNG rasterizer for favicon and OG image (not a package dependency — the implementer must generate static files)

**Missing dependencies with fallback:**
- `@fontsource-variable/poppins` and `@fontsource-variable/open-sans` — not yet installed; fallback is Google Fonts `<link>` if npm install fails

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Vitest 3.2.4 |
| Config file | `frontend/vitest.config.ts` |
| Quick run command | `npm test` (from `frontend/`) |
| Full suite command | `npm test` (from `frontend/`) |
| Test environment | happy-dom |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| BRAND-01 | Token replacement propagates to components — no gray defaults remain | Visual (manual) | — | N/A — manual-only: visual inspection in browser |
| BRAND-01 | CSS custom property `--primary` resolves to teal color | Unit (CSS token) | `npm test -- --reporter=verbose` | ❌ Wave 0 — new test needed |
| BRAND-02 | Font CSS variables resolve to Poppins/Open Sans | Visual (manual) | — | N/A — manual-only: DevTools font check |
| BRAND-03 | `document.title` updates to "Search \| Gaucho Course Optimizer" | Unit | `npm test -- --reporter=verbose` | ❌ Wave 0 — new test in SearchPage.test.tsx |
| BRAND-03 | `document.title` updates to "[Course Name] \| Gaucho Course Optimizer" on CoursePage | Unit | `npm test -- --reporter=verbose` | ❌ Wave 0 — new test in CoursePage.test.tsx |
| BRAND-03 | Score badge renders with correct color class for score >= 70 | Unit | `npm test -- src/components/ProfessorCard.test.tsx` | ✅ (existing test needs update for badge) |

### Sampling Rate

- **Per task commit:** `npm test` from `frontend/` (full suite, ~5s)
- **Per wave merge:** `npm test` (same)
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `frontend/src/pages/SearchPage.test.tsx` — covers BRAND-03 document.title behavior for Search page
- [ ] `frontend/src/pages/CoursePage.test.tsx` — covers BRAND-03 document.title behavior for Course page
- [ ] Update `frontend/src/components/ProfessorCard.test.tsx` — update score assertion from plain text `'75'` to handle Badge wrapper; add test for score badge color class per banding threshold

**Note:** CSS-in-JS / computed-style tests for BRAND-01 color tokens are impractical in happy-dom (CSSOM does not process @theme inline). Visual verification in browser is the authoritative check for color correctness.

---

## Sources

### Primary (HIGH confidence)
- `frontend/src/index.css` — Current token schema, all existing CSS variable names and format
- `frontend/src/components/ProfessorCard.tsx` — Current score display implementation
- `frontend/src/components/GradeChart.tsx`, `GpaTrendChart.tsx` — Current chart color hardcodes
- `frontend/src/components/ui/badge.tsx` — Badge API (className override via cn())
- `frontend/package.json` — Installed dependencies, confirmed Recharts 3.8.1, Vitest 3.2.4
- oklch color math (IEC 61966-2-1 + Oklab spec) — Computed directly in Node.js for verified accuracy
- OKLCH color math algorithm — Verified by cross-checking with known #FFFFFF → oklch(1 0 0) identity

### Secondary (MEDIUM confidence)
- https://fontsource.org/fonts/poppins/install — @fontsource-variable/poppins install pattern, font-family name
- https://ui.shadcn.com/docs/theming — shadcn/ui token schema, @theme inline integration
- https://web.dev/articles/building/an-adaptive-favicon — SVG favicon + PNG fallback strategy
- npm registry: `@fontsource-variable/poppins` v5.2.7, `@fontsource-variable/open-sans` v5.2.7 (verified 2026-04-02)

### Tertiary (LOW confidence — verify before implementing)
- SVG favicon browser support: caniuse.com `link-icon-svg` — SVG favicons not supported in Safari < 15.6; PNG fallback required. WebSearch only, browser support table may not reflect very latest Safari version.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified npm versions, inspected installed packages, confirmed @fontsource pattern
- Architecture: HIGH — read all canonical files listed in CONTEXT.md; token propagation path verified from `index.css` through `@theme inline` to component class names
- oklch conversions: HIGH — computed directly in Node.js using authoritative Oklab matrix math; cross-checked with known identity (white = oklch(1 0 0 0))
- Pitfalls: HIGH for font name and badge test breakage (reproducible from source); MEDIUM for CoursePage title issue (depends on actual API response structure)
- Favicon/OG: MEDIUM — browser support verified; OG absolute URL requirement confirmed from multiple sources

**Research date:** 2026-04-02
**Valid until:** 2026-07-01 (stable ecosystem — Tailwind v4, fontsource v5, shadcn/ui token schema all stable)

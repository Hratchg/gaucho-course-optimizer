# Phase 3: React Frontend - Research

**Researched:** 2026-04-01
**Domain:** React SPA — Vite + TypeScript + shadcn/ui + TanStack Query + Recharts
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Compact card by default — professor name, Gaucho Score (prominent), avg GPA, RMP quality/difficulty/WTRA, and keyword tags visible without expanding.
- **D-02:** A single expand toggle reveals BOTH sections together: grade distribution bar chart + GPA trend line chart AND the 5 most recent RMP comments with VADER sentiment badges.
- **D-03:** Gaucho Score color banding — Claude's discretion on visual implementation. Thresholds: ≥70 green, 50–69 yellow, <50 red.
- **D-04:** Collapsed card header: professor name, Gaucho Score, avg GPA, RMP quality/difficulty/"would take again", keyword tags.
- **D-05:** Desktop layout — left sidebar, always visible, sliders stay in view while scrolling.
- **D-06:** Mobile layout — shadcn/ui Sheet (bottom drawer) for sliders. "Adjust weights" button above results.
- **D-07:** Numeric weight display — show normalized weight value if it fits cleanly.
- **D-08:** Two routes: `/` (search) and `/courses/:courseId` (professor rankings).
- **D-09:** `vercel.json` rewrite: `{ "source": "/(.*)", "destination": "/index.html" }`.
- **D-10:** Navigating to `/courses/142` directly loads data from API using courseId param — self-sufficient.
- **D-11:** TanStack Query (react-query) for all API calls — loading/error/success states, caching, retry.
- **D-12:** Cold-start UX: track elapsed time since first API call. If still loading after 3 seconds, show "Waking up the server…" alongside skeleton cards.
- **D-13:** Vite + React + TypeScript.
- **D-14:** shadcn/ui + Tailwind CSS (Command for autocomplete, Skeleton for loading, Sheet for mobile, Collapsible for expand).
- **D-15:** Recharts: BarChart for grade distribution, LineChart for GPA trend. Both use `width="100%"` via ResponsiveContainer.

### Claude's Discretion
- Color banding visual implementation (colored left border strip, badge, or score text color)
- Mobile slider UI (Sheet is the obvious choice)
- Numeric weight display (show if it fits)
- TypeScript vs JavaScript (TS recommended; shadcn/ui templates use TS)
- Exact sidebar width and responsive breakpoint (Tailwind `md:` breakpoint standard)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within Phase 3 scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| UI-01 | Autocomplete course search (fires after 1–2 chars, keyboard-navigable via shadcn/ui Command) | shadcn/ui Command component + debounce + TanStack Query |
| UI-02 | Professor list ranked by Gaucho Score with color-banded score on each card | Client-side sort by computed score; color class map |
| UI-03 | Grade distribution BarChart (A+ through F, percent per grade) | Recharts BarChart + ResponsiveContainer |
| UI-04 | GPA trend LineChart (avg GPA by quarter, Y-axis 0–4.0) | Recharts LineChart + fixed YAxis domain |
| UI-05 | RMP quality, difficulty, "would take again" visible on each card | ProfessorRanking schema fields `rmp_quality`, `rmp_difficulty`, `rmp_would_take_again` |
| UI-06 | 5 most recent RMP comments with VADER sentiment badge | `/professors/{id}/comments` + badge thresholds |
| UI-07 | Four weight sliders rerank professor list instantly in browser — no API round-trip | Client-side score recompute on slider change using stored raw factors |
| UI-08 | Keyword tags on each professor card | `keywords: string[]` field in ProfessorRanking schema |
| UI-09 | Mobile-responsive: stacked cards, responsive charts, 44px touch targets | Tailwind responsive classes, Recharts ResponsiveContainer |
| UI-10 | Skeleton loading cards while API responds | shadcn/ui Skeleton component |
| UI-11 | "Waking up the server…" message after 3 seconds of loading | useEffect timer watching TanStack Query `isLoading` state |
| DEPLOY-01 | vercel.json rewrite rule for React Router deep links | Static JSON file at repo root |
</phase_requirements>

---

## Summary

Phase 3 builds a React SPA over the existing FastAPI backend. All technology choices are locked by CONTEXT.md decisions: Vite + React + TypeScript scaffolded with `npm create vite@latest`, shadcn/ui initialized via `npx shadcn@latest init`, TanStack Query v5 for data fetching, and Recharts 3.x for charts.

The frontend has no new backend work. The scoring formula is reimplemented in JavaScript as a pure function — `score = Σ(factor × normalizedWeight)` — run client-side on every slider change. The four raw factors (`gpa_factor`, `quality_factor`, `difficulty_factor`, `sentiment_factor`) are already returned by `GET /courses/{id}/professors` (confirmed in `api/schemas.py`). This eliminates all network latency on weight adjustments (D-11, UI-07).

The most complex interactions are: (1) the debounced Command autocomplete triggering a TanStack Query fetch, (2) the responsive two-column layout switching to mobile-first single column at `md:` breakpoint, and (3) the cold-start timer that shows a "Waking up…" banner after 3 seconds. All three have well-established patterns in the 2025 ecosystem.

**Primary recommendation:** Scaffold `frontend/` at project root using the shadcn/ui Vite template CLI, implement TanStack Query v5 with the single-object argument pattern, use Recharts 3.x with `<ResponsiveContainer width="100%">`, and gate all tests on MSW + Vitest + @testing-library/react.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| vite | 6.x (6.3.x latest) | Build tool + dev server | Fastest HMR, Vite = default for new React projects |
| react | 19.x (19.2.4 latest) | UI framework | Locked decision |
| react-dom | 19.x | DOM rendering | Paired with react |
| typescript | 5.x (5.8+ latest) | Type safety | shadcn/ui templates use TS; catches prop shape errors |
| @vitejs/plugin-react | 4.x | React JSX transform in Vite | Required for JSX |
| @tanstack/react-query | 5.x (5.96.x latest) | Data fetching + caching | Locked decision; v5 stable, unified object API |
| react-router-dom | 7.x (7.13.x latest) | Client-side routing | Locked decision |
| recharts | 3.x (3.8.1 latest) | Charts | Locked decision; v3 stable as of 2024 |
| tailwindcss | 4.x (4.2.x latest) | Utility CSS | Locked decision; v4 uses `@tailwindcss/vite` plugin, no postcss |
| shadcn/ui (CLI) | 0.x (0.0.4 CLI version) | Component primitives | Locked decision; installed per-component via CLI |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @radix-ui/react-dialog | 1.x | Sheet/Drawer primitive | Underpins shadcn Sheet for mobile sliders |
| class-variance-authority | 0.7.x | Variant styling API | Used internally by shadcn components |
| lucide-react | 0.x (0.9.5 latest) | Icon set | Chevrons, X buttons on cards |
| clsx | 2.x | Conditional classnames | Standard with tailwind-merge |
| tailwind-merge | 3.x | Merge Tailwind classes | Prevents class conflicts in shadcn components |

### Testing
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| vitest | 4.x (4.1.2 latest) | Test runner | Vite-native, Jest-compatible API |
| @testing-library/react | 16.x (16.3.2 latest) | Component rendering | All component tests |
| @testing-library/user-event | 14.x (14.6.1 latest) | User interaction simulation | Click, type, select |
| @testing-library/jest-dom | 6.x (6.9.1 latest) | DOM matchers | toBeInTheDocument, toHaveTextContent |
| msw | 2.x (2.12.x latest) | API mocking | Intercepts fetch() calls in jsdom tests |
| jsdom | 25.x | DOM environment for Node tests | Required by vitest + RTL |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| TanStack Query | SWR | SWR has simpler API but less control; TQ v5 is locked decision |
| Recharts | Chart.js / Nivo | Recharts is React-native, no canvas; locked decision |
| React Router v6 | TanStack Router | TanStack Router has full TS routing but heavier; React Router v6 is locked |
| shadcn/ui Collapsible | Accordion | Accordion forces only one open at a time; Collapsible allows independent cards |

**Installation (scaffold):**
```bash
# 1. Scaffold Vite + React + TS
npm create vite@latest frontend -- --template react-ts
cd frontend && npm install

# 2. Install Tailwind v4 (uses @tailwindcss/vite, NOT postcss setup)
npm install -D tailwindcss @tailwindcss/vite

# 3. Install shadcn/ui dependencies before init
npm install -D @types/node

# 4. Initialize shadcn/ui
npx shadcn@latest init

# 5. Add required shadcn components
npx shadcn@latest add command skeleton sheet collapsible card badge slider

# 6. Install runtime deps
npm install @tanstack/react-query react-router-dom recharts

# 7. Install test deps
npm install -D vitest jsdom @testing-library/react @testing-library/user-event @testing-library/jest-dom msw
```

**Version verification (confirmed 2026-04-01 via npm registry):**
- vite: 6.3.x | react: 19.2.4 | typescript: 6.0.x | @tanstack/react-query: 5.96.x
- recharts: 3.8.1 | react-router-dom: 7.13.x | vitest: 4.1.2 | msw: 2.12.x

---

## Architecture Patterns

### Recommended Project Structure
```
frontend/
├── public/                  # static assets
├── src/
│   ├── components/
│   │   ├── ui/              # shadcn auto-generated components
│   │   ├── CourseSearch.tsx  # Command autocomplete for UI-01
│   │   ├── ProfessorCard.tsx # Compact + expandable card for UI-02/03/04/05/06/08
│   │   ├── WeightSliders.tsx # Four sliders + normalization for UI-07
│   │   ├── GradeChart.tsx   # Recharts BarChart wrapper for UI-03
│   │   ├── GpaTrendChart.tsx # Recharts LineChart wrapper for UI-04
│   │   ├── SentimentBadge.tsx # VADER badge for UI-06
│   │   └── SkeletonCard.tsx  # Loading placeholder for UI-10
│   ├── hooks/
│   │   ├── useCourseSearch.ts  # TanStack Query for GET /courses/search
│   │   ├── useProfessors.ts    # TanStack Query for GET /courses/{id}/professors
│   │   ├── useProfessorGrades.ts # TanStack Query for GET /professors/{id}/grades
│   │   ├── useProfessorComments.ts # TanStack Query for GET /professors/{id}/comments
│   │   └── useElapsedTime.ts   # timer hook for cold-start UX (UI-11)
│   ├── lib/
│   │   ├── scoring.ts          # client-side score recompute function
│   │   ├── api.ts              # fetch helpers, VITE_API_URL base
│   │   └── utils.ts            # shadcn cn() utility
│   ├── pages/
│   │   ├── SearchPage.tsx      # Route: /
│   │   └── CoursePage.tsx      # Route: /courses/:courseId
│   ├── types/
│   │   └── api.ts              # TypeScript types mirroring api/schemas.py
│   ├── App.tsx                 # Router setup
│   └── main.tsx                # QueryClientProvider + RouterProvider
├── .env.local                  # VITE_API_URL=http://localhost:8000
├── vercel.json                 # DEPLOY-01 rewrite rule
├── vite.config.ts
├── tsconfig.json
└── vitest.config.ts
```

### Pattern 1: TanStack Query v5 Hook
**What:** Single-object argument `useQuery` with stable query keys
**When to use:** All four API calls

```typescript
// Source: https://tanstack.com/query/v5/docs/framework/react/reference/useQuery
// src/hooks/useProfessors.ts
import { useQuery } from '@tanstack/react-query'
import { fetchProfessors } from '@/lib/api'
import type { ProfessorRanking } from '@/types/api'

export function useProfessors(courseId: number) {
  return useQuery<ProfessorRanking[]>({
    queryKey: ['professors', courseId],
    queryFn: () => fetchProfessors(courseId),
    enabled: courseId > 0,
    retry: 3,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}
```

### Pattern 2: Client-Side Score Recompute
**What:** Pure JS function mirroring `etl/scoring.py:compute_gaucho_score()`
**When to use:** On every slider change (UI-07), must not trigger API call

```typescript
// Source: dashboard/app.py lines 31-33, etl/scoring.py
// src/lib/scoring.ts
export interface Weights {
  gpa: number
  quality: number
  difficulty: number
  sentiment: number
}

export function normalizeWeights(weights: Weights): Weights {
  const total = Object.values(weights).reduce((s, v) => s + v, 0)
  if (total === 0) return { gpa: 0.25, quality: 0.25, difficulty: 0.25, sentiment: 0.25 }
  return {
    gpa: weights.gpa / total,
    quality: weights.quality / total,
    difficulty: weights.difficulty / total,
    sentiment: weights.sentiment / total,
  }
}

export function computeGauchoScore(
  gpaFactor: number,
  qualityFactor: number,
  difficultyFactor: number,
  sentimentFactor: number,
  weights: Weights
): number {
  const w = normalizeWeights(weights)
  const raw =
    gpaFactor * w.gpa +
    qualityFactor * w.quality +
    difficultyFactor * w.difficulty +
    sentimentFactor * w.sentiment
  return Math.round(raw * 100)
}
```

### Pattern 3: Cold-Start Timer Hook (UI-11)
**What:** useEffect that starts a timer when isLoading becomes true; sets a flag at 3 seconds
**When to use:** CoursePage only

```typescript
// src/hooks/useElapsedTime.ts
import { useEffect, useState } from 'react'

export function useColdStartMessage(isLoading: boolean): boolean {
  const [showMessage, setShowMessage] = useState(false)

  useEffect(() => {
    if (!isLoading) {
      setShowMessage(false)
      return
    }
    const timer = setTimeout(() => setShowMessage(true), 3000)
    return () => clearTimeout(timer)
  }, [isLoading])

  return showMessage
}
```

### Pattern 4: Debounced Command Autocomplete (UI-01)
**What:** shadcn/ui Command wraps a controlled input; TanStack Query `enabled` gate fires only when query is >= 2 chars
**When to use:** SearchPage

```typescript
// src/components/CourseSearch.tsx (conceptual pattern)
// Use `enabled: query.trim().length >= 2` on the useQuery to prevent fetching on 0-1 chars
// CommandInput is uncontrolled by default; manage value via onValueChange
```

### Pattern 5: Recharts Responsive Chart
**What:** Always wrap in `<ResponsiveContainer width="100%" height={300}>` for UI-09
**When to use:** GradeChart and GpaTrendChart

```typescript
// Source: https://recharts.github.io/en-US/api/ResponsiveContainer
// src/components/GradeChart.tsx
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip } from 'recharts'

const GRADE_KEYS = ['a_plus','a','a_minus','b_plus','b','b_minus',
                    'c_plus','c','c_minus','d_plus','d','d_minus','f'] as const
const GRADE_LABELS = ['A+','A','A-','B+','B','B-','C+','C','C-','D+','D','D-','F']

export function GradeChart({ quarters }: { quarters: GradeQuarter[] }) {
  const data = GRADE_LABELS.map((label, i) => ({
    grade: label,
    count: quarters.reduce((sum, q) => sum + (q[GRADE_KEYS[i]] ?? 0), 0),
  }))

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: 8 }}>
        <XAxis dataKey="grade" />
        <YAxis />
        <Tooltip />
        <Bar dataKey="count" fill="#6366f1" />
      </BarChart>
    </ResponsiveContainer>
  )
}
```

### Pattern 6: GPA Trend LineChart with Fixed Y-Axis
```typescript
// Source: dashboard/app.py line 192 — yaxis_range=[0, 4.0]
// src/components/GpaTrendChart.tsx
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip } from 'recharts'

export function GpaTrendChart({ quarters }: { quarters: GradeQuarter[] }) {
  const data = quarters
    .filter(q => q.avg_gpa != null)
    .map(q => ({ quarter: q.quarter, avg_gpa: q.avg_gpa }))

  return (
    <ResponsiveContainer width="100%" height={250}>
      <LineChart data={data}>
        <XAxis dataKey="quarter" />
        <YAxis domain={[0, 4.0]} />
        <Tooltip />
        <Line type="monotone" dataKey="avg_gpa" stroke="#10b981" dot={false} />
      </LineChart>
    </ResponsiveContainer>
  )
}
```

### Pattern 7: Score Color Banding (D-03)
**Recommended implementation:** Colored left border strip (4px) — cleanest option, doesn't compete with score text, works on compact card.

```typescript
// src/components/ProfessorCard.tsx
function scoreBorderClass(score: number): string {
  if (score >= 70) return 'border-l-4 border-l-green-500'
  if (score >= 50) return 'border-l-4 border-l-yellow-500'
  return 'border-l-4 border-l-red-500'
}
```

### Pattern 8: vercel.json (DEPLOY-01)
```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```
Place at `frontend/vercel.json` (or repo root if Vercel is pointed at root). Vercel serves static assets directly; the catch-all only fires for unmatched paths, so CSS/JS assets are unaffected.

### Anti-Patterns to Avoid
- **Calling API on every slider move:** weight changes must use stored raw factors, never re-fetch.
- **Not memoizing the sorted professor list:** every slider tick re-renders — `useMemo(() => [...professors].sort(...), [professors, weights])` prevents flicker.
- **Recharts inside a zero-height container:** ResponsiveContainer needs a parent with explicit height, or pass `height={300}` directly.
- **Using `onSuccess`/`onError` callbacks in useQuery (v5 removed them):** use `useEffect` watching `data` and `error` instead.
- **Tailwind v3 `postcss.config.js` setup with v4:** Tailwind v4 uses `@tailwindcss/vite` plugin only — do NOT run `npx tailwindcss init -p`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Accessible keyboard search dropdown | Custom combobox with focus management | shadcn/ui Command (cmdk) | ARIA roles, keyboard nav, filtering built-in |
| Loading placeholder layout | Custom animated div | shadcn/ui Skeleton | Pulse animation, matches content dimensions |
| Bottom drawer on mobile | Custom CSS slide-up panel | shadcn/ui Sheet (`side="bottom"`) | Focus trap, scroll lock, escape key, backdrop |
| Expandable card section | Custom toggle with display:none | shadcn/ui Collapsible | ARIA expanded/controls, animation-ready |
| API response caching + retry | Custom fetch wrapper + localStorage | TanStack Query v5 | Stale-while-revalidate, dedup, error retry |
| Responsive chart sizing | Manual ResizeObserver | Recharts ResponsiveContainer | Handles all resize edge cases |
| Class merging | String concatenation | clsx + tailwind-merge (`cn()`) | Avoids conflicting Tailwind class specificity |

**Key insight:** shadcn/ui is not a component library — it's copy-paste primitives. Components live in `src/components/ui/` and can be edited. This means no version lock-in, but also no automatic updates. After `npx shadcn@latest add button`, the file is yours.

---

## Common Pitfalls

### Pitfall 1: Tailwind v4 vs v3 Setup Differences
**What goes wrong:** Running `npx tailwindcss init -p` (v3 pattern) creates a `tailwind.config.js` and `postcss.config.js` that conflict with v4's new plugin approach.
**Why it happens:** Tailwind v4 ships a `@tailwindcss/vite` Vite plugin. No `tailwind.config.js` needed for basic use — configuration lives in CSS.
**How to avoid:** Install `tailwindcss @tailwindcss/vite`, add `tailwindcss()` to `vite.config.ts` plugins, add `@import "tailwindcss"` to `src/index.css`. Skip `postcss.config.js` entirely.
**Warning signs:** Build output has no utility classes; `cn()` calls produce unstyled components.

### Pitfall 2: TanStack Query v5 Removed Callbacks
**What goes wrong:** `useQuery({ onSuccess: ... })` silently does nothing — the callbacks were removed in v5.
**Why it happens:** v5 unified the API and removed side-effect callbacks from useQuery.
**How to avoid:** Use `useEffect` watching `data`: `useEffect(() => { if (data) doSomething(data) }, [data])`.
**Warning signs:** TypeScript will catch this — `onSuccess` is not in the v5 types.

### Pitfall 3: React Router v6+ Requires RouterProvider Pattern
**What goes wrong:** Using `<BrowserRouter>` still works but is the legacy API; some features need `RouterProvider`.
**Why it happens:** React Router v6.4+ introduced data APIs that require `createBrowserRouter`.
**How to avoid:** For this app's simplicity (2 routes, no data loaders), `<BrowserRouter>` is fine and simpler. Use `createBrowserRouter` only if loader-based data fetching is added.
**Warning signs:** n/a for this project — both APIs are supported in v7.

### Pitfall 4: Recharts ResponsiveContainer Needs Explicit Parent Height
**What goes wrong:** Chart renders as 0-height invisible element.
**Why it happens:** `width="100%"` is fine; `height="100%"` requires the parent to have an explicit height.
**How to avoid:** Always pass explicit `height={300}` to ResponsiveContainer or set a min-height on the wrapper div.
**Warning signs:** Chart is in the DOM but visually empty; no error thrown.

### Pitfall 5: shadcn/ui Command Does Not Debounce by Default
**What goes wrong:** Every keystroke fires `onValueChange`; if TanStack Query is triggered directly, network requests flood for each character.
**Why it happens:** cmdk's CommandInput is an uncontrolled input that calls `onValueChange` synchronously.
**How to avoid:** Store input value in state, pass to `useQuery` with `enabled: value.length >= 2`, and TanStack Query's built-in dedup handles rapid refires on the same key. For true debounce, add a `useDebounce` hook with 300ms delay before the query key changes.
**Warning signs:** Network tab shows a request per keystroke.

### Pitfall 6: Grades API Requires Both professor_id AND course_id
**What goes wrong:** `GET /professors/{id}/grades` returns 422 if `course_id` query param is missing.
**Why it happens:** Grade data is per (professor, course) pair — confirmed in `api/routers/professors.py`.
**How to avoid:** Always pass `?course_id={courseId}` when fetching grades from within the CoursePage context.
**Warning signs:** 422 Unprocessable Entity in the network tab.

### Pitfall 7: Weights State Must Live at CoursePage Level
**What goes wrong:** Putting weight state inside WeightSliders component means re-renders don't propagate to the professor list.
**Why it happens:** State only flows down, not up.
**How to avoid:** Lift `weights` state to CoursePage; pass down to both `<WeightSliders>` and the professor list rendering logic. Use `useMemo` for the sorted/re-scored list.
**Warning signs:** Sliders move but list order doesn't change.

---

## TypeScript Types (from api/schemas.py)

These types must match the Pydantic schemas exactly:

```typescript
// src/types/api.ts — mirrors api/schemas.py
export interface CourseResult {
  id: number
  code: string
  title: string | null
  department: string | null
}

export interface ProfessorRanking {
  id: number
  name: string
  department: string | null
  gaucho_score: number
  gpa_factor: number
  quality_factor: number
  difficulty_factor: number
  sentiment_factor: number
  rmp_quality: number | null
  rmp_difficulty: number | null
  rmp_would_take_again: number | null
  rmp_num_ratings: number | null
  mean_gpa: number | null
  std_gpa: number | null
  avg_sentiment: number | null
  match_confidence: number | null
  quarters_taught: number
  keywords: string[]
}

export interface GradeQuarter {
  quarter: string
  avg_gpa: number | null
  a_plus: number
  a: number
  a_minus: number
  b_plus: number
  b: number
  b_minus: number
  c_plus: number
  c: number
  c_minus: number
  d_plus: number
  d: number
  d_minus: number
  f: number
}

export interface CommentResult {
  text: string | null
  sentiment_score: number | null
  keywords: string[] | null
  created_at: string | null
}
```

---

## API Endpoint Summary (for frontend calls)

| Endpoint | Method | Params | Used By |
|----------|--------|--------|---------|
| `/courses/search?q={query}` | GET | `q`: string (1–100 chars, `[a-zA-Z0-9 \-]+`) | UI-01 autocomplete |
| `/courses/{courseId}/professors` | GET | path: `courseId` int | UI-02/07 ranking page |
| `/professors/{professorId}/grades?course_id={courseId}` | GET | path: `professorId`, query: `course_id` | UI-03/04 charts (on expand) |
| `/professors/{professorId}/comments` | GET | path: `professorId`, default limit=5 | UI-06 comments (on expand) |

**API base URL:** `import.meta.env.VITE_API_URL` — `http://localhost:8000` in `.env.local`.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| CRA (create-react-app) | Vite | 2022–2023 | 10-100x faster dev server startup |
| Tailwind v3 (postcss config) | Tailwind v4 (@tailwindcss/vite) | 2025 | No postcss.config needed; CSS-based configuration |
| react-query v4 (multiple overloads) | TanStack Query v5 (single object arg) | Late 2023 | `onSuccess`/`onError` removed; `isLoading` redefined |
| Recharts v2 | Recharts v3 | 2024 | State management rewrite; `activeIndex` removed from some components |
| shadcn@0.8 (separate package) | shadcn@latest (monorepo CLI) | 2024–2025 | CLI version 0.0.4; install via `npx shadcn@latest` |
| React Router v5 | React Router v6+ (v7 latest) | Ongoing | `useHistory` → `useNavigate`; nested routes as JSX |

**Deprecated/outdated:**
- `react-scripts` (CRA): unmaintained since 2023; do not use.
- `tailwind.config.js` for v4 projects: replaced by inline CSS config.
- `useQuery({ onSuccess, onError })` callbacks: removed in TanStack Query v5.
- Recharts `<Customized>` component: no longer necessary in v3 (custom components supported natively).

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Vite + npm | ✓ | v20.9.0 | — |
| npm | Package install | ✓ | 10.1.0 | — |
| npx | shadcn CLI | ✓ | 10.1.0 | — |
| Python (FastAPI backend) | Dev data for manual testing | ✓ | 3.12.0 | Use MSW mocks for tests |
| git | Version control | ✓ | 2.44.0 | — |

**Missing dependencies with no fallback:** None — all required tools are present.

**Note:** The FastAPI backend must be running (`uvicorn api.main:app --reload`) for live dev testing. Tests use MSW and do not require the backend.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest 4.1.2 |
| Config file | `frontend/vitest.config.ts` — Wave 0 gap |
| Quick run command | `cd frontend && npm run test -- --run` |
| Full suite command | `cd frontend && npm run test` |

### Vitest + RTL + MSW Setup (Wave 0)

**`frontend/vitest.config.ts`:**
```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
  },
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
})
```

**`frontend/src/test/setup.ts`:**
```typescript
import '@testing-library/jest-dom/vitest'
import { afterEach, afterAll, beforeAll } from 'vitest'
import { cleanup } from '@testing-library/react'
import { server } from './mswServer'

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => { server.resetHandlers(); cleanup() })
afterAll(() => server.close())
```

**`frontend/src/test/mswServer.ts`:**
```typescript
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import { VITE_API_URL } from './constants'

const BASE = 'http://localhost:8000'

export const handlers = [
  http.get(`${BASE}/courses/search`, () =>
    HttpResponse.json([
      { id: 1, code: 'CMPSC 8', title: 'Intro to CS', department: 'CMPSC' },
    ])
  ),
  http.get(`${BASE}/courses/:courseId/professors`, () =>
    HttpResponse.json([/* mock ProfessorRanking array */])
  ),
  http.get(`${BASE}/professors/:professorId/grades`, () =>
    HttpResponse.json([/* mock GradeQuarter array */])
  ),
  http.get(`${BASE}/professors/:professorId/comments`, () =>
    HttpResponse.json([/* mock CommentResult array */])
  ),
]

export const server = setupServer(...handlers)
```

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| UI-01 | Course autocomplete fires query after 2 chars, renders results | component + MSW | `vitest run src/components/CourseSearch.test.tsx` | ❌ Wave 0 |
| UI-01 | Keyboard navigation selects course item | component | `vitest run src/components/CourseSearch.test.tsx` | ❌ Wave 0 |
| UI-02 | Professor list renders sorted by Gaucho Score, highest first | component | `vitest run src/components/ProfessorCard.test.tsx` | ❌ Wave 0 |
| UI-02 | Color border is green/yellow/red based on score threshold | unit | `vitest run src/lib/scoring.test.ts` | ❌ Wave 0 |
| UI-03 | GradeChart renders 13 grade labels on X-axis | component | `vitest run src/components/GradeChart.test.tsx` | ❌ Wave 0 |
| UI-04 | GpaTrendChart Y-axis domain is [0, 4.0] | component | `vitest run src/components/GpaTrendChart.test.tsx` | ❌ Wave 0 |
| UI-05 | rmp_quality, rmp_difficulty, rmp_would_take_again shown on card | component | `vitest run src/components/ProfessorCard.test.tsx` | ❌ Wave 0 |
| UI-06 | Sentiment badges: score ≥0.2 = Positive, ≤-0.2 = Negative, else Neutral | unit | `vitest run src/components/SentimentBadge.test.tsx` | ❌ Wave 0 |
| UI-07 | Re-scoring with new weights updates sort order without network call | unit | `vitest run src/lib/scoring.test.ts` | ❌ Wave 0 |
| UI-07 | Slider change triggers re-render with new order | component | `vitest run src/components/WeightSliders.test.tsx` | ❌ Wave 0 |
| UI-08 | Keyword tags render on professor card | component | `vitest run src/components/ProfessorCard.test.tsx` | ❌ Wave 0 |
| UI-09 | Mobile layout: cards stack full-width at < md breakpoint | manual (visual) | — | manual only |
| UI-09 | Touch targets ≥ 44px on interactive elements | manual (visual) | — | manual only |
| UI-10 | Skeleton cards render while isLoading=true | component | `vitest run src/components/SkeletonCard.test.tsx` | ❌ Wave 0 |
| UI-11 | "Waking up the server…" message appears after 3 seconds | unit (timer mock) | `vitest run src/hooks/useElapsedTime.test.ts` | ❌ Wave 0 |
| DEPLOY-01 | vercel.json contains correct rewrite rule | config check | `vitest run src/vercel.test.ts` | ❌ Wave 0 |

**Manual-only justifications:**
- UI-09 (mobile layout + touch targets): Requires real device or browser viewport simulation. Vitest + jsdom cannot verify CSS breakpoints or computed touch target sizes. Plan should include a manual checklist step.

### Critical Unit Tests

**`src/lib/scoring.test.ts` (UI-02, UI-07):**
- `computeGauchoScore` with equal weights + known factors → correct integer result
- `normalizeWeights` with all-zero input → equal fallback weights
- Sort order changes when gpa weight → 1.0 vs quality weight → 1.0
- Score color class: 70 → green, 69 → yellow, 50 → yellow, 49 → red

**`src/components/SentimentBadge.test.ts` (UI-06):**
- sentiment_score = 0.3 → renders "Positive" badge
- sentiment_score = -0.3 → renders "Negative" badge
- sentiment_score = 0.1 → renders "Neutral" badge
- sentiment_score = null → renders no badge or "N/A"

**`src/hooks/useElapsedTime.test.ts` (UI-11):**
- isLoading=true, advance timer 2999ms → showMessage=false
- isLoading=true, advance timer 3001ms → showMessage=true
- isLoading becomes false → showMessage resets to false

### Sampling Rate
- **Per task commit:** `cd frontend && npm run test -- --run` (all unit tests, < 30 seconds)
- **Per wave merge:** `cd frontend && npm run test` (watch + coverage)
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `frontend/vitest.config.ts` — test runner configuration
- [ ] `frontend/src/test/setup.ts` — jest-dom + MSW lifecycle
- [ ] `frontend/src/test/mswServer.ts` — shared MSW handlers
- [ ] `frontend/src/lib/scoring.test.ts` — covers UI-02, UI-07
- [ ] `frontend/src/components/SentimentBadge.test.tsx` — covers UI-06
- [ ] `frontend/src/hooks/useElapsedTime.test.ts` — covers UI-11
- [ ] Framework install: `npm install -D vitest jsdom @testing-library/react @testing-library/user-event @testing-library/jest-dom msw`

---

## Open Questions

1. **Grade data requires both professor_id and course_id as a pair**
   - What we know: `GET /professors/{id}/grades?course_id={id}` — both required (confirmed in `api/routers/professors.py`)
   - What's unclear: The CoursePage knows the courseId from the URL param, and the professorId from the ranking list. Both are available client-side before expanding the card — no additional fetch needed for the IDs.
   - Recommendation: Pass `courseId` from the URL param as context into each ProfessorCard; card uses it when fetching grades.

2. **Comments 404 if professor has no comments**
   - What we know: `GET /professors/{id}/comments` raises 404 when no comments exist (confirmed in `api/routers/professors.py`).
   - What's unclear: Whether 404 should be treated as empty state (show "No comments") or as an error.
   - Recommendation: TanStack Query `retry: false` on this endpoint; treat 404 as empty state in component, not error banner.

3. **Recharts v3 on React 19**
   - What we know: recharts 3.8.1 is the current version; React 19.2.4 is latest.
   - What's unclear: Whether recharts v3 peer dependency fully supports React 19 (v3 targets React 16–18 in peerDeps).
   - Recommendation: Install and test early (Wave 1). If peer dep warning blocks, use `--legacy-peer-deps`. This is LOW confidence — verify during setup.

---

## Sources

### Primary (HIGH confidence)
- `api/schemas.py` — Exact JSON shape for all response types
- `api/routers/courses.py` + `api/routers/professors.py` — Endpoint signatures and parameters
- `dashboard/app.py` — Reference implementation for scoring formula, chart structure, color bands
- npm registry (verified 2026-04-01) — Package versions: recharts 3.8.1, @tanstack/react-query 5.96.0, react-router-dom 7.13.2, vitest 4.1.2, msw 2.12.14

### Secondary (MEDIUM confidence)
- [shadcn/ui Vite Installation Docs](https://ui.shadcn.com/docs/installation/vite) — Tailwind v4 setup via `@tailwindcss/vite`, confirmed CLI workflow
- [TanStack Query v5 useQuery Docs](https://tanstack.com/query/v5/docs/framework/react/reference/useQuery) — Single-object API, removed callbacks confirmed
- [Recharts 3.0 Migration Guide](https://github.com/recharts/recharts/wiki/3.0-migration-guide) — ResponsiveContainer ref change, removed activeIndex
- [MSW Quick Start](https://mswjs.io/docs/quick-start/) — Node.js server setup for Vitest
- [TanStack Query v5 TypeScript Docs](https://tanstack.com/query/v5/docs/framework/react/typescript) — TS 5.4+ requirement

### Tertiary (LOW confidence)
- Recharts v3 + React 19 peer dependency compatibility — not officially confirmed; needs runtime validation during Wave 1 setup

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions verified via npm registry 2026-04-01
- Architecture: HIGH — patterns derived directly from existing codebase (schemas.py, dashboard/app.py) + official docs
- Pitfalls: HIGH — Tailwind v4 postcss trap and TanStack v5 callback removal are documented breaking changes
- Testing: MEDIUM — MSW + Vitest + RTL is the standard 2025 pattern; Recharts renderability in jsdom is LOW confidence (charts render SVG, may need ResizeObserver mock)

**Research date:** 2026-04-01
**Valid until:** 2026-05-01 (stable stack; shadcn components are copy-paste so no version drift)

---

## RESEARCH COMPLETE

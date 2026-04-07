# Phase 6: Navigation & Routing - Research

**Researched:** 2026-04-07
**Domain:** React Router v7 client-side navigation, persistent layout pattern, breadcrumbs, mobile Sheet drawer
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- Search moves to `/search` — frees `/` for the Tutorial Landing Page in Phase 7
- `/` gets a minimal placeholder Home page with hero text and "Start Searching" CTA — navigable but lightweight, replaced by Phase 7
- Shared `Layout.tsx` component wraps all routes using React Router `<Outlet/>` — navbar + breadcrumbs render once, pages swap inside
- Sticky top navbar with GCO logo/text on the left, nav links (Home, Search) on the right, brand teal (`#0F766E`) background
- Breadcrumb format: `Home > Search > CMPSC 130A` with chevron (`>`) separators
- Breadcrumbs render below the navbar in a horizontal strip with subtle background
- No breadcrumbs on the Home page
- Course results breadcrumb shows actual course code from URL params (e.g., "CMPSC 130A"), not generic "Course Results"
- Hamburger icon on the right side of the navbar
- Mobile menu uses shadcn/ui Sheet component sliding from the right — already in dependencies
- Desktop/mobile breakpoint at `md` (768px)
- Menu auto-closes on link click, outside tap, and Escape key press

### Claude's Discretion

- Exact navbar height and padding
- Breadcrumb component structure (single component vs separate Breadcrumb + BreadcrumbItem)
- Placeholder Home page layout and copy
- Transition animations for Sheet drawer
- NavLink active state styling approach

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| NAV-01 | User can navigate between Home, Search, and Course Results pages via a persistent top navbar | Layout.tsx + Outlet pattern; NavLink active state |
| NAV-02 | User can see their current location via breadcrumbs on interior pages (e.g., Home > Search > CMPSC 130A) | useLocation() + useParams() breadcrumb logic |
| NAV-03 | User can navigate the app on mobile via a responsive hamburger menu | shadcn Sheet component, controlled open/close state |
| NAV-04 | User can use browser back/forward buttons and deep-link directly to any page | BrowserRouter (already set up) + vercel.json SPA rewrite (already configured) + route registration |
</phase_requirements>

---

## Summary

Phase 6 is a well-scoped routing and layout phase. All required dependencies are already installed and configured — `react-router-dom` v7.13.2 is in `package.json`, `BrowserRouter` is already in `main.tsx`, the shadcn/ui `Sheet` component is already in `frontend/src/components/ui/sheet.tsx`, and `vercel.json` already has the SPA rewrite rule. No new packages are required.

The core work is four new files (`Layout.tsx`, `Navbar.tsx`, `Breadcrumbs.tsx`, `MobileMenu.tsx`), one new page (`HomePage.tsx`), a restructured `App.tsx` (Layout wrapper + route changes), and minor updates to existing pages (`SearchPage.tsx` moves from `/` to `/search`). The UI-SPEC.md provides complete visual specifications for every element, and the design tokens in `index.css` cover all required colors.

The main technical consideration is the Layout + Outlet pattern in React Router v7, which is stable and identical to v6 for declarative `<Routes>`/`<Route>` usage. The `NavLink` component's `className` callback, the `end` prop for exact-match active detection at `/`, and the `useLocation()` hook for breadcrumb route detection are the key APIs to use correctly.

**Primary recommendation:** Build four focused components (`Layout`, `Navbar`, `Breadcrumbs`, `MobileMenu`), restructure `App.tsx` to nest all routes under `<Layout>`, and keep all implementation within the existing file/folder conventions. Zero new dependencies needed.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| react-router-dom | 7.13.2 (installed) | Client-side routing, NavLink, Outlet, useLocation, useParams | Already installed; BrowserRouter configured in main.tsx |
| shadcn/ui Sheet | Installed (components/ui/sheet.tsx) | Mobile nav drawer sliding from right | Already installed; matches brand design system |
| lucide-react | ^1.7.0 (installed) | Menu, ChevronRight, Home, Search icons | Already installed; used throughout codebase |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Tailwind v4 | ^4.2.2 (installed) | Responsive classes (md: breakpoint), spacing, color tokens | All styling; `md:` at 768px for desktop/mobile split |
| clsx / tailwind-merge | installed | Conditional class composition | NavLink active state class merging |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| shadcn Sheet for mobile | Custom drawer | Sheet already installed, has Radix a11y primitives (Escape, focus trap, outside click) |
| useLocation() for breadcrumbs | React context/store | useLocation() is simpler, co-located logic, no extra state |
| NavLink className callback | Custom active tracking with useState | NavLink callback is the official pattern; avoids redundant state |

**Installation:**

No new packages needed. All dependencies are installed.

**Version verification:** [VERIFIED: node_modules inspection]
- `react-router-dom`: 7.13.2 installed
- `lucide-react`: ^1.7.0 in package.json
- `radix-ui` (Sheet uses `radix-ui` Dialog primitive): ^1.4.3 installed

---

## Architecture Patterns

### Recommended Project Structure

```
frontend/src/
├── components/
│   ├── ui/              # shadcn primitives (sheet.tsx already here)
│   ├── Navbar.tsx       # NEW — sticky top bar with logo + nav links + hamburger
│   ├── Breadcrumbs.tsx  # NEW — conditional breadcrumb strip
│   └── MobileMenu.tsx   # NEW — Sheet-based mobile nav drawer
├── layouts/
│   └── Layout.tsx       # NEW — Navbar + Breadcrumbs + <Outlet />
├── pages/
│   ├── HomePage.tsx     # NEW — placeholder home at /
│   ├── SearchPage.tsx   # EXISTING — moves from / to /search
│   └── CoursePage.tsx   # EXISTING — stays at /courses/:courseId
└── App.tsx              # MODIFIED — Layout wrapper + route restructure
```

Note: `Layout.tsx` could live in `components/` if `layouts/` feels like over-engineering for three pages. Either is acceptable; `layouts/` is conventional for "wrapper not UI widget" distinction.

### Pattern 1: Layout + Outlet Route Nesting

**What:** A parent `<Route element={<Layout />}>` wraps all child routes. The Layout renders `<Outlet />` where page content goes. This renders Navbar and Breadcrumbs exactly once, shared across all pages.

**When to use:** Any time multiple pages share a persistent shell (nav, footer, breadcrumbs).

**Example:**
```tsx
// Source: react-router-dom v7.13.2 — node_modules/react-router/dist
// App.tsx
import { Routes, Route } from 'react-router-dom'
import Layout from '@/layouts/Layout'
import HomePage from '@/pages/HomePage'
import SearchPage from '@/pages/SearchPage'
import CoursePage from '@/pages/CoursePage'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/courses/:courseId" element={<CoursePage />} />
      </Route>
    </Routes>
  )
}
```

**Layout.tsx:**
```tsx
// Source: react-router-dom v7.13.2
import { Outlet } from 'react-router-dom'
import Navbar from '@/components/Navbar'
import Breadcrumbs from '@/components/Breadcrumbs'

export default function Layout() {
  return (
    <>
      <Navbar />
      <Breadcrumbs />
      <Outlet />
    </>
  )
}
```

### Pattern 2: NavLink with className Callback

**What:** NavLink's `className` prop accepts a function `({ isActive }) => string`. This is the official way to style active links without managing separate state.

**When to use:** Any nav link that needs active/inactive visual distinction.

**Example:**
```tsx
// Source: react-router-dom v7.13.2 — NavLinkRenderProps type confirmed in node_modules
import { NavLink } from 'react-router-dom'

// For the "/" home link — use `end` prop to prevent matching on /search etc.
// NOTE: Per the v7 docs, NavLink to="/" already ignores `end` by default
// and only matches at exact root. `end` is safe to include for clarity.
<NavLink
  to="/"
  end
  className={({ isActive }) =>
    isActive
      ? 'font-bold text-white'
      : 'text-white/80 hover:text-white transition-colors'
  }
>
  Home
</NavLink>

// For /search link — no `end` needed (no child routes under /search)
<NavLink
  to="/search"
  className={({ isActive }) =>
    isActive
      ? 'font-bold text-white'
      : 'text-white/80 hover:text-white transition-colors'
  }
>
  Search
</NavLink>
```

**Key fact:** NavLink automatically adds `aria-current="page"` when active. [VERIFIED: node_modules type defs — "Automatically applies `aria-current="page"` to the link when the link is active"]

### Pattern 3: Breadcrumb Route Detection with useLocation + useParams

**What:** `useLocation()` gives `{ pathname }` — use pathname to determine which breadcrumbs to render. `useParams()` is NOT usable in Breadcrumbs (it's a sibling of page content, not a child of the Route). Instead, parse the courseId from `pathname` directly.

**When to use:** Breadcrumbs that reflect current URL structure.

**Example:**
```tsx
// Source: react-router-dom v7.13.2
import { Link, useLocation } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'

export default function Breadcrumbs() {
  const { pathname } = useLocation()

  // No breadcrumbs on home
  if (pathname === '/') return null

  // /search → Home > Search
  if (pathname === '/search') {
    return (
      <nav aria-label="Breadcrumb" className="bg-muted/50 border-b border-border px-4 md:px-6 py-2">
        <ol className="flex items-center gap-1 text-sm">
          <li>
            <Link to="/" className="text-muted-foreground hover:text-foreground">Home</Link>
          </li>
          <li aria-hidden="true"><ChevronRight className="h-3.5 w-3.5 text-muted-foreground" /></li>
          <li className="text-accent font-medium">Search</li>
        </ol>
      </nav>
    )
  }

  // /courses/:courseId → Home > Search > CMPSC 130A
  const courseMatch = pathname.match(/^\/courses\/(.+)$/)
  if (courseMatch) {
    const rawId = courseMatch[1]
    // Format: "cmpsc-130a" → "CMPSC 130A"
    const courseLabel = rawId.replace(/-/g, ' ').toUpperCase()
    return (
      <nav aria-label="Breadcrumb" className="bg-muted/50 border-b border-border px-4 md:px-6 py-2">
        <ol className="flex items-center gap-1 text-sm">
          <li><Link to="/" className="text-muted-foreground hover:text-foreground">Home</Link></li>
          <li aria-hidden="true"><ChevronRight className="h-3.5 w-3.5 text-muted-foreground" /></li>
          <li><Link to="/search" className="text-muted-foreground hover:text-foreground">Search</Link></li>
          <li aria-hidden="true"><ChevronRight className="h-3.5 w-3.5 text-muted-foreground" /></li>
          <li className="text-accent font-medium">{courseLabel}</li>
        </ol>
      </nav>
    )
  }

  return null
}
```

**Why not `useParams()` in Breadcrumbs:** `useParams()` only works within a Route that matches the param. `Breadcrumbs` renders inside `Layout` which is a parent Route with no `:courseId` param — so `useParams()` would return `{}`. Parsing `pathname` directly is the correct approach for shared layout breadcrumbs. [VERIFIED: React Router v7 docs behavior — useParams reads params from the closest matching Route]

### Pattern 4: Mobile Sheet with Controlled Close-on-Navigate

**What:** The Sheet can be uncontrolled (Sheet manages open state via SheetTrigger) or controlled (`open`/`onOpenChange` props). For auto-close on link click, use controlled mode: wrap each link in a click handler that calls `setOpen(false)`, OR use `SheetClose asChild` wrapping each link.

**When to use:** Any Sheet that should close after an interaction inside it.

**Example — SheetClose asChild approach (simpler, no useState needed):**
```tsx
// Source: sheet.tsx already in codebase — SheetClose is a Radix Dialog.Close
import { Sheet, SheetTrigger, SheetContent, SheetClose, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { Link } from 'react-router-dom'
import { Menu } from 'lucide-react'

export default function MobileMenu() {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <button aria-label="Open navigation menu" className="flex md:hidden p-2 min-h-[44px] min-w-[44px] items-center justify-center text-primary-foreground">
          <Menu className="h-5 w-5" />
        </button>
      </SheetTrigger>
      <SheetContent side="right">
        <SheetHeader>
          <SheetTitle>Gaucho Course Optimizer</SheetTitle>
        </SheetHeader>
        <nav className="flex flex-col mt-4">
          <SheetClose asChild>
            <Link to="/" className="py-3 px-4 text-base font-sans min-h-[44px] flex items-center">
              Home
            </Link>
          </SheetClose>
          <SheetClose asChild>
            <Link to="/search" className="py-3 px-4 text-base font-sans min-h-[44px] flex items-center">
              Search
            </Link>
          </SheetClose>
        </nav>
      </SheetContent>
    </Sheet>
  )
}
```

**Why SheetClose asChild:** Escape key and outside tap are already handled by the Radix Dialog primitive under the Sheet. SheetClose asChild handles the "link click" case without extra state. [VERIFIED: sheet.tsx in codebase uses `SheetPrimitive.Close` = Radix Dialog.Close; Radix Dialog handles Escape and outside click automatically]

### Anti-Patterns to Avoid

- **Using `useParams()` in Layout-level Breadcrumbs:** Returns empty object because Layout Route has no path params. Parse `pathname` from `useLocation()` instead.
- **Wrapping `BrowserRouter` in `main.tsx` again:** It's already there. Adding another router context breaks the app.
- **Using `window.location.pathname` instead of `useLocation()`:** Won't trigger re-renders on client navigation; React Router's `useLocation()` is reactive.
- **Not adding `end` prop to NavLink to="/":** Without it, `NavLink to="/"` would mark "Home" as active on every page (it technically would not in v7 due to a special case, but using `end` is explicit and safe).
- **Forgetting `aria-hidden="true"` on chevron separators in breadcrumbs:** Screen readers would read out chevron icons as noise.
- **Setting `sticky top-0` without `z-50`:** Other elements with default stacking will overlap the navbar.
- **CoursePage sticky sidebar uses `top-6`:** After adding a `h-14` sticky navbar, the sidebar sticky offset should be updated to `top-[calc(3.5rem+1.5rem)]` or `top-20` to avoid being hidden under the navbar. This is a coordination item between Phase 6 and CoursePage.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Escape key + outside click to close mobile drawer | Custom event listeners | Radix Dialog primitive (via Sheet) | Already handled by SheetPrimitive.Root |
| Focus trap inside open Sheet | Manual focus management | Radix Dialog primitive (via Sheet) | Radix automatically traps focus in modals/sheets |
| Active link detection | useState + useEffect + pathname comparison | NavLink className callback | NavLink is reactive, handles edge cases, auto-sets aria-current |
| SPA deep-link support | Server-side config | vercel.json (already configured) | Rewrite rule `"source": "/(.*)"` → `/index.html` already in place |
| Route-based breadcrumb state | Global state/context | useLocation() pathname parsing | No state needed; pathname is the single source of truth |

**Key insight:** Radix primitives handle the hardest accessibility and interaction problems (focus management, keyboard dismissal, aria roles) in the Sheet component. Don't rebuild any of this.

---

## Runtime State Inventory

> Not applicable — this is a greenfield layout/routing phase, not a rename/refactor/migration phase.

---

## Common Pitfalls

### Pitfall 1: CoursePage sticky sidebar offset after adding sticky navbar

**What goes wrong:** CoursePage desktop layout has `<div className="sticky top-6">` for the weight sliders sidebar. After adding a `h-14` (56px) sticky navbar, the sidebar will be visually hidden under the navbar when it sticks.

**Why it happens:** `top-6` (24px) does not account for the 56px navbar height.

**How to avoid:** Update CoursePage's sticky sidebar to `top-[calc(3.5rem+1.5rem)]` or `top-20` (80px = 56px navbar + 24px original offset). Plan this as an explicit sub-task.

**Warning signs:** Sidebar appears to disappear or overlap with navbar content when scrolling on CoursePage.

### Pitfall 2: NavLink active state matching `/` on all routes

**What goes wrong:** By default, `NavLink to="/"` would mark Home as active on `/search` and `/courses/:courseId` too, because `/` is a prefix of all paths.

**Why it happens:** React Router's default matching is prefix-based for NavLink.

**How to avoid:** In React Router v7, the `NavLink to="/"` has a special-cased behavior that it only matches the root (`/`) exactly, similar to `end` being applied automatically. However, adding `end` explicitly is safe and makes intent clear. [VERIFIED: node_modules docs — "`<NavLink to="/">` is an exceptional case... it effectively ignores the `end` prop and only matches when you're at the root route"]

### Pitfall 3: useParams() returns {} inside Layout component

**What goes wrong:** If `Breadcrumbs` is placed inside `Layout` (which it is), and you call `useParams()` to get `courseId` for the course breadcrumb, it returns an empty object.

**Why it happens:** `useParams()` only exposes params from the matched Route that contains the component. `Layout` wraps all routes with `element={<Layout />}` and no path params; the `:courseId` param is in the child `Route path="/courses/:courseId"`.

**How to avoid:** Parse `courseId` from `useLocation().pathname` using a regex: `/^\/courses\/(.+)$/`.

### Pitfall 4: Sheet not closing on navigation in uncontrolled mode

**What goes wrong:** If Sheet is used in uncontrolled mode (no `open`/`onOpenChange`), clicking a Link inside it closes the Sheet via Radix's Dialog.Close only if the Link is wrapped in `SheetClose`. Without the wrapper, the Sheet stays open and the navigation occurs in the background.

**Why it happens:** React Router `Link` does not call any sheet close handler; the Sheet's internal open state is only changed by its own Radix events.

**How to avoid:** Wrap every nav `Link` inside the Sheet with `<SheetClose asChild>`. This is confirmed in the UI-SPEC interaction contract.

### Pitfall 5: Missing `aria-label` on hamburger button

**What goes wrong:** Screen readers announce the button as just "button" with no context.

**Why it happens:** Icon-only buttons have no visible text.

**How to avoid:** Always add `aria-label="Open navigation menu"` to the hamburger button, and toggle to `"Close navigation menu"` when open (or let SheetClose handle that via the X button in SheetContent). The UI-SPEC requires this explicitly.

---

## Code Examples

Verified patterns from codebase and library sources:

### Rendering Outlet in a Layout

```tsx
// Source: react-router-dom v7.13.2 — confirmed Outlet export in node_modules
import { Outlet } from 'react-router-dom'

export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <Breadcrumbs />
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  )
}
```

### Route nesting with Layout wrapper

```tsx
// Source: react-router-dom v7 — Routes/Route API confirmed in node_modules
<Routes>
  <Route element={<Layout />}>
    <Route path="/" element={<HomePage />} />
    <Route path="/search" element={<SearchPage />} />
    <Route path="/courses/:courseId" element={<CoursePage />} />
  </Route>
</Routes>
```

### NavLink active state (exact pattern from UI-SPEC)

```tsx
// Source: react-router-dom v7 NavLinkRenderProps — confirmed in node_modules
<NavLink
  to="/search"
  className={({ isActive }) =>
    isActive ? 'font-bold text-white' : 'text-white/80 hover:text-white'
  }
>
  Search
</NavLink>
```

### Testing components that use routing

```tsx
// Source: existing codebase pattern (CoursePage.test.tsx, CourseSearch.test.tsx)
// Wrap in MemoryRouter for isolated component tests
import { MemoryRouter, Route, Routes } from 'react-router-dom'

function renderWithRouter(path = '/') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/search" element={<SearchPage />} />
        </Route>
      </Routes>
    </MemoryRouter>
  )
}
```

### Testing NavLink active state

```tsx
// MemoryRouter sets the initial location; NavLink className callback is reactive
render(
  <MemoryRouter initialEntries={['/search']}>
    <Navbar />
  </MemoryRouter>
)
const searchLink = screen.getByRole('link', { name: /search/i })
expect(searchLink).toHaveClass('font-bold')
expect(searchLink).toHaveAttribute('aria-current', 'page')
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| React Router v5 `Switch` + `Redirect` | `Routes` + `Route` + `Navigate` | React Router v6 (2021) | `Switch` is gone; use `Routes` |
| React Router v5 `component=` prop | `element=` prop with JSX | React Router v6 (2021) | Must use `<Component />` not `Component` |
| Separate `react-router` + `react-router-dom` | Unified package | React Router v7 (2024) | Only need `react-router-dom`; `react-router` is a peer dep |
| Custom active link state | `NavLink className callback` | React Router v5+ | Official API; auto sets `aria-current` |

**Deprecated/outdated:**
- `Switch`: Replaced by `Routes` — not available in v7
- `useHistory`: Replaced by `useNavigate` — not used in this phase but worth noting
- Separate `history` package: Built into React Router v6+

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | courseId URL format uses hyphens (e.g., `cmpsc-130a`) for the breadcrumb label formatting logic | Architecture Patterns / Pattern 3 | Breadcrumb label would format incorrectly. Verify actual courseId format by inspecting how CourseSearch navigates to `/courses/:courseId` | 

**Verification path for A1:** Check `CourseSearch.tsx` navigation call — how does it construct the URL when selecting a course? If courseId is numeric (e.g., `/courses/42`), the breadcrumb cannot show a human-readable course code from the URL alone and would need to read from another source or use a fallback label.

---

## Open Questions

1. **What is the actual courseId format in the URL?**
   - What we know: `CoursePage.tsx` calls `Number(courseId)` suggesting it may be a numeric ID (e.g., `/courses/42`), not a code like `cmpsc-130a`
   - What's unclear: If courseId is numeric, `rawId.replace(/-/g, ' ').toUpperCase()` would produce "42", not "CMPSC 130A"
   - Recommendation: Check `CourseSearch.tsx` to see how it navigates to `/courses/:courseId`. The UI-SPEC says "reads `courseId` URL param, formats as uppercase course code" — this implies the courseId IS the course code (hyphenated). But `CoursePage.tsx`'s `Number(courseId)` implies it's numeric. The planner should resolve this before implementing Breadcrumbs.

2. **Does `SearchPage.tsx` header text need updating after moving to `/search`?**
   - What we know: `SearchPage.tsx` currently has `<h1>Gaucho Course Optimizer</h1>` as a page heading
   - What's unclear: Now that there's a Navbar with the brand name and a Home page, this h1 may be redundant or inconsistent
   - Recommendation: Plan a sub-task to clean up SearchPage's existing heading content when moving it to `/search`

---

## Environment Availability

> Step 2.6: SKIPPED — This phase is purely frontend code changes. No external tools, services, or CLIs beyond the existing project stack are required. All dependencies (`react-router-dom`, `shadcn Sheet`, `lucide-react`) are already installed in `node_modules`.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Vitest 3.2.4 + React Testing Library 16.3.2 |
| Config file | `frontend/vitest.config.ts` (exists) |
| Quick run command | `cd frontend && npm test -- --reporter=verbose` |
| Full suite command | `cd frontend && npm test` |

Vitest config uses `happy-dom` environment. Setup file at `frontend/src/test/setup.ts` initializes `@testing-library/jest-dom` matchers and MSW server.

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| NAV-01 | Navbar renders on all pages with Home and Search links | unit | `cd frontend && npm test -- Navbar` | ❌ Wave 0 |
| NAV-01 | NavLink shows active state on current page | unit | `cd frontend && npm test -- Navbar` | ❌ Wave 0 |
| NAV-02 | Breadcrumbs render Home > Search on /search | unit | `cd frontend && npm test -- Breadcrumbs` | ❌ Wave 0 |
| NAV-02 | Breadcrumbs render Home > Search > {course} on /courses/:id | unit | `cd frontend && npm test -- Breadcrumbs` | ❌ Wave 0 |
| NAV-02 | No breadcrumbs rendered on / (Home page) | unit | `cd frontend && npm test -- Breadcrumbs` | ❌ Wave 0 |
| NAV-03 | Hamburger button visible on mobile (md breakpoint test) | unit | `cd frontend && npm test -- MobileMenu` | ❌ Wave 0 |
| NAV-03 | Sheet opens on hamburger click | unit | `cd frontend && npm test -- MobileMenu` | ❌ Wave 0 |
| NAV-03 | Sheet closes after link click | unit | `cd frontend && npm test -- MobileMenu` | ❌ Wave 0 |
| NAV-04 | App.tsx routes registered correctly (/ /search /courses/:id) | unit | `cd frontend && npm test -- App` | ❌ Wave 0 |
| NAV-04 | HomePage renders at / | unit | `cd frontend && npm test -- HomePage` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `cd frontend && npm test -- --reporter=dot`
- **Per wave merge:** `cd frontend && npm test`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `frontend/src/components/Navbar.test.tsx` — covers NAV-01 (active links, renders on all pages)
- [ ] `frontend/src/components/Breadcrumbs.test.tsx` — covers NAV-02 (route-conditional rendering)
- [ ] `frontend/src/components/MobileMenu.test.tsx` — covers NAV-03 (open/close behavior)
- [ ] `frontend/src/pages/HomePage.test.tsx` — covers NAV-04 (page renders at /)
- [ ] `frontend/src/App.test.tsx` — covers NAV-04 (route structure, no 404 on direct URLs)

**Testing pattern to follow (from existing codebase):**
- Use `MemoryRouter` with `initialEntries` to test route-dependent behavior
- Wrap with `QueryClientProvider` when rendering full pages
- Use `describe` + `it` blocks with Vitest
- Test file co-located with component (`Navbar.test.tsx` next to `Navbar.tsx`)

---

## Security Domain

> Applicable ASVS categories for this phase:

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No auth in this phase |
| V3 Session Management | no | No sessions |
| V4 Access Control | no | All routes are public |
| V5 Input Validation | minimal | `courseId` from URL params is passed to `Number()` in CoursePage — already existing; breadcrumb label formatting uses `.replace()` + `.toUpperCase()` on URL segment (no XSS vector since React escapes JSX) |
| V6 Cryptography | no | No crypto needed |

**No new security concerns introduced.** This phase adds client-side navigation only. `vercel.json` SPA rewrites are already in place. React's JSX escaping prevents XSS from URL-derived breadcrumb labels.

---

## Sources

### Primary (HIGH confidence)

- [VERIFIED: node_modules/react-router-dom@7.13.2] — NavLink, NavLinkRenderProps (`isActive`, `isPending`, `isTransitioning`), `end` prop, `aria-current="page"` auto-application, Outlet, useLocation, MemoryRouter
- [VERIFIED: node_modules/react-router/dist/development/index-react-server-client-CCwMoQIT.d.ts] — Full type signatures for NavLinkProps, NavLinkRenderProps, OutletProps
- [VERIFIED: frontend/src/components/ui/sheet.tsx] — Sheet, SheetClose, SheetContent, SheetTrigger, SheetHeader, SheetTitle exports; `side="right"` default; Radix Dialog primitive underneath
- [VERIFIED: frontend/src/index.css] — All CSS custom properties: `--primary`, `--accent`, `--background`, `--muted`, `--muted-foreground`, `--border`; font tokens `--font-heading`, `--font-sans`
- [VERIFIED: frontend/package.json] — react-router-dom ^7.13.2, lucide-react ^1.7.0, radix-ui ^1.4.3
- [VERIFIED: frontend/src/main.tsx] — BrowserRouter already configured
- [VERIFIED: frontend/vercel.json] — SPA rewrite `"source": "/(.*)"` → `"/index.html"` already in place
- [VERIFIED: frontend/src/App.tsx] — Current route structure (`/` → SearchPage, `/courses/:courseId` → CoursePage)
- [VERIFIED: frontend/vitest.config.ts] — happy-dom environment, setup file, @/ alias
- [VERIFIED: frontend/src/test/setup.ts + mswServer.ts] — MSW server setup pattern
- [VERIFIED: frontend/src/pages/CoursePage.test.tsx + SearchPage.test.tsx] — MemoryRouter + initialEntries test pattern
- [VERIFIED: .planning/phases/06-navigation-routing/06-UI-SPEC.md] — Complete component specs, interaction contracts, copy

### Secondary (MEDIUM confidence)

- [CITED: React Router v7 node_modules docs inline] — `NavLink to="/"` special-cased behavior for root route (matches only exact root)
- [CITED: sheet.tsx source] — Radix SheetPrimitive.Close (Dialog.Close) automatically handles Escape key and outside tap dismissal

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all dependencies verified in node_modules and package.json
- Architecture: HIGH — patterns verified against installed library type definitions and existing codebase test conventions
- Pitfalls: HIGH (sticky offset, aria), MEDIUM (courseId format question — flagged as open question)
- Test patterns: HIGH — existing test files show exact patterns to follow

**Research date:** 2026-04-07
**Valid until:** 2026-07-07 (React Router v7 stable API; shadcn Sheet stable)

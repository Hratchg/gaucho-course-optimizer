# Phase 6: Navigation & Routing - Context

**Gathered:** 2026-04-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Build a persistent navigation system with client-side routing across three pages (Home, Search, Course Results). Add a shared Layout component with top navbar, breadcrumb trail, and mobile hamburger drawer. Move Search from `/` to `/search`, place a placeholder Home at `/`, and ensure all routes support direct URL access and browser history.

</domain>

<decisions>
## Implementation Decisions

### Route Structure & Page Layout
- Search moves to `/search` — frees `/` for the Tutorial Landing Page in Phase 7
- `/` gets a minimal placeholder Home page with hero text and "Start Searching" CTA — navigable but lightweight, replaced by Phase 7
- Shared `Layout.tsx` component wraps all routes using React Router `<Outlet/>` — navbar + breadcrumbs render once, pages swap inside
- Sticky top navbar with GCO logo/text on the left, nav links (Home, Search) on the right, brand teal (#0F766E) background

### Breadcrumbs & Navigation UX
- Breadcrumb format: `Home > Search > CMPSC 130A` with chevron (`>`) separators — matches ROADMAP example
- Breadcrumbs render below the navbar in a horizontal strip with subtle background — visually distinct from page content
- No breadcrumbs on the Home page — Home is root, breadcrumbs are redundant there
- Course results breadcrumb shows actual course code from URL params (e.g., "CMPSC 130A"), not generic "Course Results"

### Mobile Navigation
- Hamburger icon on the right side of the navbar — standard mobile pattern
- Mobile menu uses shadcn/ui Sheet component sliding from the right — already in dependencies, brand-consistent
- Desktop/mobile breakpoint at `md` (768px) — matches existing Tailwind responsive breakpoints
- Menu auto-closes on link click, outside tap, and Escape key press

### Claude's Discretion
- Exact navbar height and padding
- Breadcrumb component structure (single component vs separate Breadcrumb + BreadcrumbItem)
- Placeholder Home page layout and copy
- Transition animations for Sheet drawer
- NavLink active state styling approach

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `react-router-dom` v7.13.2 already installed with `BrowserRouter` in `main.tsx`
- shadcn/ui `Sheet` component available at `frontend/src/components/ui/sheet.tsx`
- Brand tokens in `frontend/src/index.css` — Deep Teal primary, Amber accent
- `lucide-react` icons available (Menu, ChevronRight, Home, Search icons)

### Established Patterns
- Routes defined in `App.tsx` using `<Routes>` and `<Route>`
- Pages live in `frontend/src/pages/` (SearchPage.tsx, CoursePage.tsx)
- Components in `frontend/src/components/`
- shadcn/ui primitives in `frontend/src/components/ui/`
- Tailwind v4 with `@theme inline` in index.css
- Tests use Vitest + React Testing Library in `*.test.tsx` files

### Integration Points
- `App.tsx` — needs Layout wrapper and route restructuring
- `main.tsx` — BrowserRouter already set up, no changes needed
- `SearchPage.tsx` — moves from `/` to `/search`
- `CoursePage.tsx` — stays at `/courses/:courseId`, breadcrumb reads `courseId` param
- `vercel.json` — already has SPA rewrites configured

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches matching existing codebase patterns.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

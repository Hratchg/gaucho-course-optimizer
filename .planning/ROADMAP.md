# Roadmap: Gaucho Course Optimizer

## Milestone v1.0: Foundation to Public App (COMPLETED 2026-04-02)

v1.0 took a working but internal Python ETL pipeline and exposed it as a public-facing web app. The work proceeded in four sequential phases: fix the data layer so the API is fast, build the API so the frontend has a contract, build the frontend so students can actually use it, then deploy so it's public.

### v1.0 Phases

- [x] **Phase 1: Foundation & Bug Fixes** - Verify the ETL pipeline end-to-end, fix critical bugs, and establish a clean data layer on Neon PostgreSQL
- [x] **Phase 2: FastAPI Backend** - Build and test five REST endpoints that expose course search, professor ranking, grade data, comments, and health check
- [x] **Phase 3: React Frontend** - Build the full student-facing SPA with course search, professor cards, charts, weight sliders, and mobile-responsive layout
- [x] **Phase 4: Deployment** - Deploy both services publicly, configure CORS, and set up cold-start mitigation

### v1.0 Phase Details

#### Phase 1: Foundation & Bug Fixes
**Goal**: The data layer is verified, performant, and safe to build on — pipeline runs end-to-end against Neon, critical bugs are fixed, and tests cover core scoring logic
**Depends on**: Nothing (first phase)
**Requirements**: FDN-01, FDN-02, FDN-03, FDN-04, FDN-05, FDN-06, TEST-01, TEST-02
**Success Criteria** (what must be TRUE):
  1. Developer can run the full ETL pipeline (scrape -> match -> NLP -> score) and confirm professor-course records with Gaucho Scores are present in the Neon database
  2. Developer can run `pytest` and see pipeline tests (scraping, matching, scoring) pass with mocked HTTP -- no real calls to RMP or Daily Nexus
  3. Developer can run `pytest` and see Gaucho Score formula tests pass for known inputs
  4. Application handles concurrent API requests -- connection pool is configured and the database does not exhaust connections under load
  5. Professor ranking query executes as a single JOIN, and database foreign-key indexes exist so queries remain fast as data grows
**Plans:** 4 plans (all complete)
**Status**: Complete (2026-03-31)

#### Phase 2: FastAPI Backend
**Goal**: Five REST endpoints are live, tested against a fixture database, and return correctly shaped data ready for React consumption -- including raw factor values that enable client-side score recomputation
**Depends on**: Phase 1
**Requirements**: API-01, API-02, API-03, API-04, API-05, TEST-03, TEST-04
**Success Criteria** (what must be TRUE):
  1. Developer can call `GET /health` and receive `{"status": "ok"}` with no database query
  2. Developer can call `GET /courses/search?q=physics` and receive up to 20 validated results -- input with special characters or excessive length is rejected
  3. Developer can call `GET /courses/{id}/professors` and receive a ranked list with Gaucho Score, raw factor values, RMP metrics, and keyword tags
  4. Developer can call `GET /professors/{id}/grades` and `GET /professors/{id}/comments` and receive correctly shaped data
  5. Developer can run `pytest` and see all endpoint tests pass using the test database session fixture
**Plans:** 5 plans (all complete)
**Status**: Complete (2026-04-01)

#### Phase 3: React Frontend
**Goal**: UCSB students can search for any course, see professors ranked by Gaucho Score with all supporting data visible, adjust weights to rerank instantly in the browser, and use the app on a phone
**Depends on**: Phase 2
**Requirements**: UI-01, UI-02, UI-03, UI-04, UI-05, UI-06, UI-07, UI-08, UI-09, UI-10, UI-11
**Success Criteria** (what must be TRUE):
  1. Student can type a partial course name or code and see autocomplete suggestions appear, navigable by keyboard, firing after 1-2 characters
  2. Student can select a course and see all professors ranked by Gaucho Score with color-banded score indicators, grade distribution bar charts, GPA trend line charts, RMP metrics, keyword tags, and the 5 most recent RMP comments with VADER sentiment badges
  3. Student can drag four weight sliders and see the professor list rerank instantly in the browser with no API round-trip
  4. Student can use the app on a mobile phone -- professor cards stack full-width, charts resize responsively, all interactive elements have adequate touch targets
  5. Student sees skeleton loading cards while the API responds, and a "Waking up the server..." message appears after 3 seconds of waiting
**Plans:** 7 plans (all complete)
**Status**: Complete (2026-04-01)

#### Phase 4: Deployment
**Goal**: Both services are live at public URLs, CORS is correctly scoped to the production Vercel domain, and the Render service stays warm during UCSB registration hours
**Depends on**: Phase 3
**Requirements**: DEPLOY-01, DEPLOY-02, DEPLOY-03
**Success Criteria** (what must be TRUE):
  1. Student can access the React SPA at a public Vercel URL and navigate directly to `/course/:id` deep links without a 404
  2. Student's browser can make API calls from the Vercel URL to the Render service without CORS errors -- no wildcard origins in production
  3. Render API service responds within normal latency during UCSB registration hours -- UptimeRobot pings `/health` every 10 minutes to prevent cold starts
**Plans:** 2 plans (all complete)
**Status**: Complete (2026-04-02)

---

## Milestone v1.1: UI/UX Overhaul (COMPLETED)

v1.1 transforms the functional MVP into a polished, branded experience. All changes are frontend-only (React + Vite + Tailwind + shadcn/ui). The work proceeds in four natural phases: establish the design system first so every subsequent phase inherits consistent tokens, wire up routing and navigation so pages can exist, build the tutorial content that lives on the home page, then replace the weight sliders with the new toggle-based control system.

### v1.1 Phases

- [x] **Phase 5: Branding & Design System** - Apply the Deep Teal + Amber color scheme, professional typography, and brand identity (favicon, meta tags) globally across all pages and components
- [x] **Phase 6: Navigation & Routing** - Build a persistent top navbar with page routing, breadcrumb navigation, responsive hamburger menu, and browser history support
- [x] **Phase 7: Tutorial Landing Page** - Build the home page with a visual Gaucho Score breakdown, factor definitions, step-by-step usage guide, and a prominent CTA to begin searching
- [x] **Phase 8: Weight Controls Overhaul** - Replace sliders with student-friendly toggle checkboxes, implement auto-distributed equal weighting, and confirm instant re-ranking on the results page

### v1.1 Phase Details

#### Phase 5: Branding & Design System
**Goal**: Every page and component reflects the Deep Teal + Amber visual identity -- design tokens are the single source of truth and typography is set globally
**Depends on**: Phase 4
**Requirements**: BRAND-01, BRAND-02, BRAND-03
**Success Criteria** (what must be TRUE):
  1. Student sees Deep Teal (#0F766E) primary color and Amber (#D97706) accent color applied consistently across all interactive elements, headings, and highlights -- no legacy gray or blue defaults remain
  2. Student sees a professional heading font and a distinct, readable body font applied globally -- fonts load without flash of unstyled text
  3. Student sees the Gaucho Course Optimizer favicon in the browser tab on all pages
  4. Student sees a descriptive page title in the browser tab (not the default "Vite App") that updates per page
  5. When a student shares a link, the Open Graph preview shows the correct title, description, and image
**Plans:** 2 plans (all complete)
**Status**: Complete
**UI hint**: yes

#### Phase 6: Navigation & Routing
**Goal**: Students can move between Home, Search, and Course Results pages via a persistent navbar, always know where they are, and use the browser naturally including back/forward buttons and direct URLs
**Depends on**: Phase 5
**Requirements**: NAV-01, NAV-02, NAV-03, NAV-04
**Success Criteria** (what must be TRUE):
  1. Student can see a top navbar on every page with links to Home and Search, and click any link to navigate without a full page reload
  2. Student on an interior page (Search or Course Results) can see breadcrumbs showing their path (e.g., Home > Search > CMPSC 130A) and click any breadcrumb to navigate back to that level
  3. Student on a mobile device can tap a hamburger icon to open a navigation menu and tap any link to navigate -- the menu closes after selection
  4. Student can paste a direct URL to any page (e.g., `/course/cmpsc-130a`) into a new browser tab and land on the correct page without a 404 or redirect to home
**Plans:** 2 plans (all complete)
**Status**: Complete
**UI hint**: yes

#### Phase 7: Tutorial Landing Page
**Goal**: A student who has never used the app can land on the home page, understand exactly how Gaucho Score works and what each factor means, follow a clear usage guide, and confidently start searching
**Depends on**: Phase 6
**Requirements**: TUT-01, TUT-02, TUT-03, TUT-04
**Success Criteria** (what must be TRUE):
  1. Student can see a visual diagram or breakdown on the home page showing how the four factors (GPA, Quality, Difficulty, Sentiment) combine into a 0-100 Gaucho Score
  2. Student can read a clear definition and real example for each of the four scoring factors -- no jargon, no unexplained acronyms
  3. Student can follow a step-by-step guide on the home page (at least three steps) that walks through searching a course and interpreting the results
  4. Student can click a prominent call-to-action button on the home page that takes them directly to the Search page to begin finding professors
**Plans:** 1 plan (all complete)
**Status**: Complete
**UI hint**: yes

#### Phase 8: Weight Controls Overhaul
**Goal**: Students control professor ranking through four clearly labeled toggle checkboxes rather than numeric sliders -- selected factors share weight equally, and the ranking updates instantly on every toggle
**Depends on**: Phase 7
**Requirements**: WGHT-01, WGHT-02
**Success Criteria** (what must be TRUE):
  1. Student on the Course Results page sees four toggle checkboxes labeled "Easy Grades", "Great Teaching", "Low Difficulty", and "Good Reviews" instead of numeric sliders
  2. Student can toggle any checkbox on or off and see the professor ranking update immediately in the browser with no loading spinner or API call
  3. Student who enables two checkboxes sees those two factors weighted equally in the ranking, while disabled factors are de-emphasized -- the weighting logic is transparent (e.g., labels or tooltips explain the distribution)
**Plans:** 1 plan (all complete)
**Status**: Complete
**UI hint**: yes

---

## Milestone v1.2: Data Quality & Insights (COMPLETED 2026-04-08)

v1.2 surfaced more meaningful, actionable information on professor cards -- active teaching badges, per-quarter grade distributions, and curated keyword tags. See [v1.2-ROADMAP.md](milestones/v1.2-ROADMAP.md) for full details.

### v1.2 Phases

- [x] **Phase 9: Active Teaching** - Compute active teaching status from grade history, expose it in the API, and display badges, quarter history, and a filter on professor cards
- [x] **Phase 10: Grade Distribution by Quarter** - Enrich the grades API with per-quarter breakdowns, default the chart to the most recent quarter, and add a quarter selector with an all-time toggle (completed 2026-04-08)
- [x] **Phase 11: Standardized Keywords** - Define a curated tag vocabulary, map raw NLP output to standard labels with frequency filtering in the ETL pipeline, and display filterable tags with review-count tooltips (completed 2026-04-08)

### v1.2 Phase Details

### Phase 9: Active Teaching
**Goal**: Students can immediately see which professors are actively teaching a course, filter out inactive professors, and view the specific quarters each professor has taught
**Depends on**: Phase 8
**Requirements**: TEACH-01, TEACH-02, TEACH-03
**Success Criteria** (what must be TRUE):
  1. Student searching a course sees an "Actively Teaching" badge on professor cards for any professor who taught the course 3 or more times in the past 3 years -- professors who do not meet this threshold have no badge
  2. Student can click a filter toggle to show only actively teaching professors, and the list updates immediately to hide inactive professors
  3. Student can see which specific quarters (e.g., "Fall 2024", "Winter 2025") a professor taught the searched course -- this information is visible on the professor card or in an expandable detail
  4. The active teaching computation runs server-side so the badge and quarter list are present in the API response without requiring additional client-side requests
**Plans**: 2/2 complete
**Status**: Complete (2026-04-08)
**UI hint**: yes

### Phase 10: Grade Distribution by Quarter
**Goal**: Students see the most recent quarter's grade distribution by default instead of an all-time aggregate, and can drill into any specific quarter or switch to the combined historical view
**Depends on**: Phase 9
**Requirements**: GRADE-01, GRADE-02, GRADE-03
**Success Criteria** (what must be TRUE):
  1. Student viewing a professor's grade chart sees the most recent quarter's distribution (e.g., "Winter 2025") displayed by default -- not the all-time aggregate that was previously shown
  2. Student can select a specific quarter from a dropdown menu and see the grade chart update to show only that quarter's distribution
  3. Student can toggle between "Most Recent" and "All Quarters Combined" views, and the chart reflects the selected mode immediately
  4. The quarter dropdown lists all available quarters in reverse chronological order, and the selected quarter's label is clearly visible above or within the chart
**Plans:** 1/1 plans complete
Plans:
- [x] 10-01-PLAN.md -- Install shadcn Select, add quarter filtering to GradeChart, add quarter selector dropdown to ProfessorCard, update tests
**UI hint**: yes

### Phase 11: Standardized Keywords
**Goal**: Professor cards display a curated set of meaningful, human-readable tags instead of raw NLP-extracted words, with noise filtering so only frequently mentioned attributes appear
**Depends on**: Phase 10
**Requirements**: KW-01, KW-02, KW-03
**Success Criteria** (what must be TRUE):
  1. Student viewing a professor card sees tags drawn from a curated vocabulary of 15-20 labels (e.g., "Easy Grader", "Tough Exams", "Engaging Lectures", "Heavy Homework") instead of raw single-word NLP extractions
  2. Tags only appear on a professor card if the underlying concept was mentioned in 3 or more reviews for that professor -- low-frequency noise words are absent
  3. Student can hover (or tap on mobile) any tag to see a tooltip showing how many reviews mentioned it (e.g., "Easy Grader -- 7 reviews")
  4. The curated vocabulary mapping and frequency filtering are computed during the ETL pipeline, not at request time -- the API serves pre-computed tags
**Plans:** 2/2 plans complete
Plans:
- [x] 11-01-PLAN.md -- Backend tag vocabulary, mapping function with frequency filtering, schema change, backend tests
- [x] 11-02-PLAN.md -- Frontend tag badge display with review-count tooltips, TypeScript types, MSW mock update
**UI hint**: yes

---

## Milestone v2.0: Visual Redesign & UX Overhaul

v2.0 replaces the Deep Teal + Amber design system with a Royal Blue + Snow White palette, swaps Poppins/Open Sans for Inter, adds WCAG AA accessibility throughout, introduces a micro-animation system, and overhauls every component to use the new tokens. All changes are frontend-only (React + CSS). The work proceeds in four phases: establish design tokens and typography first so every subsequent phase inherits the new visual language, then layer in accessibility patterns as cross-cutting infrastructure, build the animation primitives as reusable utilities, and finally overhaul every component applying all three layers together.

### v2.0 Phases

- [ ] **Phase 12: Design Tokens & Typography** - Replace color palette with Royal Blue + Snow White, swap to Inter font, and establish the type scale as foundation for all subsequent phases
- [ ] **Phase 13: Accessibility** - Add WCAG AA contrast, focus rings, aria-labels, keyboard navigation, skip-to-content, and reduced-motion support across the app
- [ ] **Phase 14: Animations & Interactions** - Build micro-interaction primitives (button press, card hover, page transitions, staggered lists, skeleton shimmer) as reusable utilities
- [ ] **Phase 15: Component Overhaul** - Redesign every user-facing component (cards, navbar, breadcrumbs, search, charts, mobile menu, tutorial, badges) using new tokens, a11y patterns, and animations

### v2.0 Phase Details

### Phase 12: Design Tokens & Typography
**Goal**: Every CSS custom property and font reference in the app uses the new Royal Blue + Snow White color system and Inter typography -- the old Deep Teal + Amber palette and Poppins/Open Sans fonts are completely gone
**Depends on**: Phase 11
**Requirements**: DESIGN-01, DESIGN-02, DESIGN-03, TYPE-01, TYPE-02
**Success Criteria** (what must be TRUE):
  1. Student sees Royal Blue (#2563EB) as the primary color and Snow (#FAFBFF) as the page background across all pages -- no Deep Teal or Amber colors remain anywhere in the UI
  2. Student sees Inter as the sole font on all text (headings, body, labels, buttons) -- no Poppins or Open Sans font references remain in the codebase
  3. All text conforms to the 4-size type scale (14px labels, 16px body, 20px headings, 28px display) -- no arbitrary or one-off font sizes exist
  4. Grade distribution charts use a blue-family color palette where each bar/segment maintains at least 3:1 contrast against its neighbors and the chart background
  5. Score badges retain their green/yellow/red semantic colors with updated values that meet 4.5:1 contrast ratio against white card backgrounds
**Plans**: 1 plan
Plans:
- [ ] 12-01-PLAN.md -- Swap fonts to Inter, replace all CSS tokens with Royal Blue + Snow White palette, update chart colors and score badges
**UI hint**: yes

### Phase 13: Accessibility
**Goal**: The app meets WCAG AA accessibility standards -- all text is readable, all interactive elements are keyboard-navigable with visible focus indicators, and users who prefer reduced motion see a calm, animation-free experience
**Depends on**: Phase 12
**Requirements**: A11Y-01, A11Y-02, A11Y-03, A11Y-04, A11Y-05, A11Y-06
**Success Criteria** (what must be TRUE):
  1. All text in the app meets WCAG AA contrast ratios (4.5:1 for normal text, 3:1 for large text) when inspected against its actual background color -- no contrast failures remain
  2. Student using keyboard-only navigation can tab through all interactive elements in visual order, sees a visible focus ring (2-4px) on each focused element, and can activate buttons/links with Enter or Space
  3. Every icon-only button (hamburger menu, close buttons, chart controls) has an aria-label that screen readers announce -- no unlabeled interactive icons exist
  4. Student pressing Tab immediately after page load can activate a "Skip to content" link that jumps past the navbar to the main content area
  5. Student with prefers-reduced-motion enabled in their OS sees no non-essential animations -- page transitions, card hover effects, and staggered list entrances are suppressed
**Plans**: TBD
**UI hint**: yes

### Phase 14: Animations & Interactions
**Goal**: The app feels responsive and alive through consistent micro-interactions -- buttons give tactile feedback, cards lift on hover, pages transition smoothly, professor lists animate in, and loading states shimmer instead of sitting static
**Depends on**: Phase 13
**Requirements**: ANIM-01, ANIM-02, ANIM-03, ANIM-04, ANIM-05
**Success Criteria** (what must be TRUE):
  1. Student pressing any button sees it scale down slightly (to 0.97) with a subtle shadow change over 150ms, giving tactile press feedback
  2. Student hovering over any professor card sees it lift with an elevated shadow over 200ms ease-out -- the card returns to its resting state when the cursor leaves
  3. Student navigating between pages sees a smooth fade + subtle slide transition (200ms) rather than an instant hard cut between views
  4. Student viewing a course results page sees professor cards animate in with staggered timing (30-50ms delay between each card) rather than all appearing simultaneously
  5. Student waiting for API data sees skeleton cards with an animated shimmer effect sweeping across them, replacing the previous static gray skeleton placeholders
**Plans**: TBD
**UI hint**: yes

### Phase 15: Component Overhaul
**Goal**: Every user-facing component has been redesigned with the Royal Blue + Snow White tokens, Inter typography, accessibility patterns, and animation system -- the visual refresh is complete and cohesive across the entire app
**Depends on**: Phase 14
**Requirements**: COMP-01, COMP-02, COMP-03, COMP-04, COMP-05, COMP-06, COMP-07, COMP-08
**Success Criteria** (what must be TRUE):
  1. Student viewing professor cards sees the redesigned layout with Royal Blue accents, Inter typography, updated spacing, and the new animation behaviors (hover lift, staggered entrance) applied
  2. Student sees the navbar with a Royal Blue background and Inter font, breadcrumbs with new accent colors, and the mobile Sheet menu styled with the new design tokens -- all navigation components are visually consistent
  3. Student using course search sees updated input styling (Royal Blue focus ring, Inter font) and a restyled dropdown with the new color palette
  4. Student viewing grade charts sees the blue-family palette with improved axis labels, consistent typography, and proper contrast -- charts feel integrated with the new design system rather than like a foreign element
  5. Student viewing the tutorial landing page sees the redesigned layout with the new visual system, and all badges (score badges, active teaching badges, keyword tags) use the new palette consistently
**Plans**: TBD
**UI hint**: yes

## Progress

**Execution Order:**
v1.0 phases (1-4) complete. v1.1 phases (5-8) complete. v1.2 phases (9-11) complete. v2.0 phases execute in order: 12 -> 13 -> 14 -> 15

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Bug Fixes | 4/4 | Complete | 2026-03-31 |
| 2. FastAPI Backend | 5/5 | Complete | 2026-04-01 |
| 3. React Frontend | 7/7 | Complete | 2026-04-01 |
| 4. Deployment | 2/2 | Complete | 2026-04-02 |
| 5. Branding & Design System | 2/2 | Complete | - |
| 6. Navigation & Routing | 2/2 | Complete | - |
| 7. Tutorial Landing Page | 1/1 | Complete | - |
| 8. Weight Controls Overhaul | 1/1 | Complete | - |
| 9. Active Teaching | 2/2 | Complete | 2026-04-08 |
| 10. Grade Distribution by Quarter | 1/1 | Complete | 2026-04-08 |
| 11. Standardized Keywords | 2/2 | Complete | 2026-04-08 |
| 12. Design Tokens & Typography | 0/1 | In progress | - |
| 13. Accessibility | 0/0 | Not started | - |
| 14. Animations & Interactions | 0/0 | Not started | - |
| 15. Component Overhaul | 0/0 | Not started | - |

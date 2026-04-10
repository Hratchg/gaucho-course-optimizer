# Requirements: Gaucho Course Optimizer

**Defined:** 2026-04-02
**Core Value:** Students can search any UCSB course and instantly see which professor will give them the best outcome — ranked by a score combining GPA, RMP quality, difficulty, and sentiment

## v1.0 Requirements (Completed)

All v1.0 requirements shipped. See MILESTONES.md for details.

- [x] Foundation & Bug Fixes (FDN-01 through FDN-06)
- [x] Testing (TEST-01 through TEST-04)
- [x] FastAPI Backend (API-01 through API-05)
- [x] React Frontend (UI-01 through UI-11)
- [x] Deployment (DEPLOY-01 through DEPLOY-03)

## v1.1 Requirements (Completed)

All v1.1 requirements shipped.

### Branding & Theming

- [x] **BRAND-01**: User sees a cohesive Deep Teal (#0F766E) + Amber (#D97706) color scheme across all pages and components
- [x] **BRAND-02**: User sees professional typography with a distinct heading and body font pairing
- [x] **BRAND-03**: User sees a custom favicon, descriptive page titles, and Open Graph meta tags when sharing links

### Navigation

- [x] **NAV-01**: User can navigate between Home, Search, and Course Results pages via a persistent top navbar
- [x] **NAV-02**: User can see their current location via breadcrumbs on interior pages (e.g., Home > Search > CMPSC 130A)
- [x] **NAV-03**: User can navigate the app on mobile via a responsive hamburger menu
- [x] **NAV-04**: User can use browser back/forward buttons and deep-link directly to any page

### Tutorial Landing Page

- [x] **TUT-01**: User can see a visual breakdown of how Gaucho Score is calculated
- [x] **TUT-02**: User can read clear definitions of each scoring factor (GPA, Quality, Difficulty, Sentiment) with examples
- [x] **TUT-03**: User can follow a step-by-step guide showing how to search courses and interpret results
- [x] **TUT-04**: User can click a prominent CTA from the tutorial to begin searching courses

### Weight Controls

- [x] **WGHT-01**: User can toggle student-friendly checkboxes ("Easy Grades", "Great Teaching", "Low Difficulty", "Good Reviews") instead of adjusting sliders
- [x] **WGHT-02**: User sees professors re-ranked instantly based on which toggles are active, with selected factors getting equal emphasis and unselected factors de-emphasized

## v1.2 Requirements (Completed)

Requirements for Data Quality & Insights milestone. Each maps to roadmap phases.

### Active Teaching

- [x] **TEACH-01**: Student can see an "Actively Teaching" badge on professor cards for professors who taught the course 3+ times in the past 3 years
- [x] **TEACH-02**: Student can filter the professor list to show only actively teaching professors
- [x] **TEACH-03**: Student can see which specific quarters a professor taught the course

### Grade Distribution

- [x] **GRADE-01**: Student sees the most recent quarter's grade distribution by default (not all-time aggregate)
- [x] **GRADE-02**: Student can select a specific quarter from a dropdown to view that quarter's grade distribution
- [x] **GRADE-03**: Student can toggle between "Most Recent" and "All Quarters Combined" views

### Standardized Keywords

- [x] **KW-01**: Professor cards display tags from a curated vocabulary of ~15-20 meaningful labels (e.g., "Easy Grader", "Tough Exams", "Engaging Lectures") instead of raw NLP-extracted words
- [x] **KW-02**: Tags only appear if mentioned in 3+ reviews for that professor (noise filtering)
- [x] **KW-03**: Student can hover a tag to see how many reviews mentioned it (e.g., "Easy Grader — 7 reviews")

## v2.0 Requirements

Requirements for Visual Redesign & UX Overhaul milestone.

### Design Tokens

- [x] **DESIGN-01**: All CSS custom properties use Royal Blue (#2563EB) primary, Snow (#FAFBFF) background, white cards, near-black (#111827) text
- [x] **DESIGN-02**: Chart colors use a blue-family palette maintaining data readability and 3:1 contrast
- [x] **DESIGN-03**: Score badge colors preserved (green/yellow/red) with updated values meeting 4.5:1 contrast on white cards

### Typography

- [x] **TYPE-01**: Inter replaces Poppins and Open Sans as the sole font family across all text
- [x] **TYPE-02**: All font sizes conform to a strict 4-size scale (14px label, 16px body, 20px heading, 28px display)

### Accessibility

- [x] **A11Y-01**: All text meets WCAG AA contrast ratios (4.5:1 normal, 3:1 large)
- [x] **A11Y-02**: All interactive elements have visible focus rings (2-4px)
- [x] **A11Y-03**: All icon-only buttons have aria-labels
- [x] **A11Y-04**: Full keyboard navigation (tab order matches visual order, Enter/Space activation)
- [x] **A11Y-05**: Skip-to-content link on every page
- [x] **A11Y-06**: prefers-reduced-motion respected (disables non-essential animations)

### Animations & Interactions

- [x] **ANIM-01**: Button press feedback (scale 0.97 + subtle shadow change, 150ms)
- [x] **ANIM-02**: Card hover elevation (shadow lift, 200ms ease-out)
- [x] **ANIM-03**: Page transitions (fade + subtle slide, 200ms)
- [x] **ANIM-04**: Staggered list entrance for professor cards (30-50ms per item)
- [x] **ANIM-05**: Skeleton loading shimmer replaces static skeleton cards

### Component Overhaul

- [ ] **COMP-01**: Professor cards redesigned with new color system and spacing
- [ ] **COMP-02**: Navbar updated with Royal Blue background and Inter typography
- [ ] **COMP-03**: Breadcrumbs styled with new accent colors
- [ ] **COMP-04**: Course search updated with new input styling and dropdown
- [ ] **COMP-05**: Grade charts use new blue palette with improved axis styling
- [ ] **COMP-06**: Mobile menu (Sheet) updated with new design tokens
- [ ] **COMP-07**: Tutorial landing page redesigned with new visual system
- [ ] **COMP-08**: All badges (score, active teaching, tags) use new palette

## Future Requirements

Deferred to future release.

### Advanced Personalization

- **PERS-01**: User can save preferred toggle configurations as presets
- **PERS-02**: User can see recommended toggle configurations based on their major

### Data Features

- Professor side-by-side comparison view
- Data freshness timestamp in footer
- Recently viewed courses (localStorage)
- Dark mode toggle

## Out of Scope

| Feature | Reason |
|---------|--------|
| User accounts / login | Auth not needed for UI redesign |
| Backend changes | v2.0 is frontend-only |
| Dark mode toggle | Design tokens prepared but toggle deferred to v2.1 |
| Comparing professors side-by-side | Different UX paradigm, future milestone |
| Review submission | RMP already collects reviews |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| BRAND-01 | Phase 5 | Complete |
| BRAND-02 | Phase 5 | Complete |
| BRAND-03 | Phase 5 | Complete |
| NAV-01 | Phase 6 | Complete |
| NAV-02 | Phase 6 | Complete |
| NAV-03 | Phase 6 | Complete |
| NAV-04 | Phase 6 | Complete |
| TUT-01 | Phase 7 | Complete |
| TUT-02 | Phase 7 | Complete |
| TUT-03 | Phase 7 | Complete |
| TUT-04 | Phase 7 | Complete |
| WGHT-01 | Phase 8 | Complete |
| WGHT-02 | Phase 8 | Complete |
| TEACH-01 | Phase 9 | Complete |
| TEACH-02 | Phase 9 | Complete |
| TEACH-03 | Phase 9 | Complete |
| GRADE-01 | Phase 10 | Complete |
| GRADE-02 | Phase 10 | Complete |
| GRADE-03 | Phase 10 | Complete |
| KW-01 | Phase 11 | Complete |
| KW-02 | Phase 11 | Complete |
| KW-03 | Phase 11 | Complete |
| DESIGN-01 | Phase 12 | Complete |
| DESIGN-02 | Phase 12 | Complete |
| DESIGN-03 | Phase 12 | Complete |
| TYPE-01 | Phase 12 | Complete |
| TYPE-02 | Phase 12 | Complete |
| A11Y-01 | Phase 13 | Complete |
| A11Y-02 | Phase 13 | Complete |
| A11Y-03 | Phase 13 | Complete |
| A11Y-04 | Phase 13 | Complete |
| A11Y-05 | Phase 13 | Complete |
| A11Y-06 | Phase 13 | Complete |
| ANIM-01 | Phase 14 | Complete |
| ANIM-02 | Phase 14 | Complete |
| ANIM-03 | Phase 14 | Complete |
| ANIM-04 | Phase 14 | Complete |
| ANIM-05 | Phase 14 | Complete |
| COMP-01 | Phase 15 | Pending |
| COMP-02 | Phase 15 | Pending |
| COMP-03 | Phase 15 | Pending |
| COMP-04 | Phase 15 | Pending |
| COMP-05 | Phase 15 | Pending |
| COMP-06 | Phase 15 | Pending |
| COMP-07 | Phase 15 | Pending |
| COMP-08 | Phase 15 | Pending |

**Coverage:**
- v1.1 requirements: 14 total, 14 mapped (Complete)
- v1.2 requirements: 9 total, 9 mapped (Complete)
- v2.0 requirements: 24 total, 24 mapped (Pending)
- Unmapped: 0

---
*Requirements defined: 2026-04-02*
*Last updated: 2026-04-09 -- v2.0 traceability mapped (Phases 12-15)*

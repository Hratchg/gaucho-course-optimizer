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

## v1.2 Requirements

Requirements for Data Quality & Insights milestone. Each maps to roadmap phases.

### Active Teaching

- [ ] **TEACH-01**: Student can see an "Actively Teaching" badge on professor cards for professors who taught the course 3+ times in the past 3 years
- [ ] **TEACH-02**: Student can filter the professor list to show only actively teaching professors
- [ ] **TEACH-03**: Student can see which specific quarters a professor taught the course

### Grade Distribution

- [ ] **GRADE-01**: Student sees the most recent quarter's grade distribution by default (not all-time aggregate)
- [ ] **GRADE-02**: Student can select a specific quarter from a dropdown to view that quarter's grade distribution
- [ ] **GRADE-03**: Student can toggle between "Most Recent" and "All Quarters Combined" views

### Standardized Keywords

- [ ] **KW-01**: Professor cards display tags from a curated vocabulary of ~15-20 meaningful labels (e.g., "Easy Grader", "Tough Exams", "Engaging Lectures") instead of raw NLP-extracted words
- [ ] **KW-02**: Tags only appear if mentioned in 3+ reviews for that professor (noise filtering)
- [ ] **KW-03**: Student can hover a tag to see how many reviews mentioned it (e.g., "Easy Grader — 7 reviews")

## Future Requirements

Deferred to future release. Tracked but not in current roadmap.

### Advanced Personalization

- **PERS-01**: User can save preferred toggle configurations as presets
- **PERS-02**: User can see recommended toggle configurations based on their major

### Data Features

- Professor side-by-side comparison view
- Data freshness timestamp in footer
- Recently viewed courses (localStorage)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Dark mode | Adds complexity; single polished theme is sufficient |
| User accounts / login | Auth not needed for data quality improvements |
| Comparing professors side-by-side | Different UX paradigm, future milestone |
| Grade curve predictions | Not enough data to be reliable |
| Custom tag creation by users | Requires auth system |
| Review submission | RMP already collects reviews |
| AI chatbot / natural language query | GauchoClass already does this |
| Course schedule builder | UCSBPlat already does this |

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
| TEACH-01 | Phase 9 | Pending |
| TEACH-02 | Phase 9 | Pending |
| TEACH-03 | Phase 9 | Pending |
| GRADE-01 | Phase 10 | Pending |
| GRADE-02 | Phase 10 | Pending |
| GRADE-03 | Phase 10 | Pending |
| KW-01 | Phase 11 | Pending |
| KW-02 | Phase 11 | Pending |
| KW-03 | Phase 11 | Pending |

**Coverage:**
- v1.2 requirements: 9 total
- Mapped to phases: 9
- Unmapped: 0

---
*Requirements defined: 2026-04-02*
*Last updated: 2026-04-08 -- v1.2 traceability mapped (Phases 9-11)*

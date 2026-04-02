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

## v1.1 Requirements

Requirements for UI/UX Overhaul milestone. Each maps to roadmap phases.

### Branding & Theming

- [ ] **BRAND-01**: User sees a cohesive Deep Teal (#0F766E) + Amber (#D97706) color scheme across all pages and components
- [ ] **BRAND-02**: User sees professional typography with a distinct heading and body font pairing
- [ ] **BRAND-03**: User sees a custom favicon, descriptive page titles, and Open Graph meta tags when sharing links

### Navigation

- [ ] **NAV-01**: User can navigate between Home, Search, and Course Results pages via a persistent top navbar
- [ ] **NAV-02**: User can see their current location via breadcrumbs on interior pages (e.g., Home > Search > CMPSC 130A)
- [ ] **NAV-03**: User can navigate the app on mobile via a responsive hamburger menu
- [ ] **NAV-04**: User can use browser back/forward buttons and deep-link directly to any page

### Tutorial Landing Page

- [ ] **TUT-01**: User can see a visual breakdown of how Gaucho Score is calculated
- [ ] **TUT-02**: User can read clear definitions of each scoring factor (GPA, Quality, Difficulty, Sentiment) with examples
- [ ] **TUT-03**: User can follow a step-by-step guide showing how to search courses and interpret results
- [ ] **TUT-04**: User can click a prominent CTA from the tutorial to begin searching courses

### Weight Controls

- [ ] **WGHT-01**: User can toggle student-friendly checkboxes ("Easy Grades", "Great Teaching", "Low Difficulty", "Good Reviews") instead of adjusting sliders
- [ ] **WGHT-02**: User sees professors re-ranked instantly based on which toggles are active, with selected factors getting equal emphasis and unselected factors de-emphasized

## Future Requirements

Deferred to future release. Tracked but not in current roadmap.

### Advanced Personalization

- **PERS-01**: User can save preferred toggle configurations as presets
- **PERS-02**: User can see recommended toggle configurations based on their major

### Data Features

- Quarter-by-quarter grade filter dropdown
- Professor side-by-side comparison view
- Data freshness timestamp in footer
- Recently viewed courses (localStorage)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Dark mode | Adds complexity; single polished theme is sufficient for v1.1 |
| User accounts / login | Auth not needed for UI/UX improvements |
| Backend changes | This milestone is frontend-only |
| Animated page transitions | Nice-to-have but not essential for v1.1 polish |
| Slider controls (keeping old UX) | Being replaced by toggles |
| Review submission | RMP already collects reviews |
| AI chatbot / natural language query | GauchoClass already does this |
| Course schedule builder | UCSBPlat already does this |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| BRAND-01 | Phase 5 | Pending |
| BRAND-02 | Phase 5 | Pending |
| BRAND-03 | Phase 5 | Pending |
| NAV-01 | Phase 6 | Pending |
| NAV-02 | Phase 6 | Pending |
| NAV-03 | Phase 6 | Pending |
| NAV-04 | Phase 6 | Pending |
| TUT-01 | Phase 7 | Pending |
| TUT-02 | Phase 7 | Pending |
| TUT-03 | Phase 7 | Pending |
| TUT-04 | Phase 7 | Pending |
| WGHT-01 | Phase 8 | Pending |
| WGHT-02 | Phase 8 | Pending |

**Coverage:**
- v1.1 requirements: 13 total
- Mapped to phases: 13
- Unmapped: 0

---
*Requirements defined: 2026-04-02*
*Last updated: 2026-04-02 — Traceability filled in after roadmap creation*

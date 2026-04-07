---
phase: 06
slug: navigation-routing
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-07
---

# Phase 06 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest 3.2.4 + React Testing Library 16.3.2 |
| **Config file** | `frontend/vitest.config.ts` |
| **Quick run command** | `cd frontend && npx vitest run --reporter=dot` |
| **Full suite command** | `cd frontend && npx vitest run --reporter=verbose` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npx vitest run --reporter=dot`
- **After every wave merge:** Run `cd frontend && npx vitest run --reporter=verbose`
- **Phase gate:** Full suite green before `/gsd-verify-work`

---

## Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| NAV-01 | Navbar renders on all pages with Home and Search links | unit | `cd frontend && npx vitest run src/components/Navbar.test.tsx` | No (Wave 1) |
| NAV-01 | NavLink shows active state on current page | unit | `cd frontend && npx vitest run src/components/Navbar.test.tsx` | No (Wave 1) |
| NAV-02 | Breadcrumbs render Home > Search on /search | unit | `cd frontend && npx vitest run src/components/Breadcrumbs.test.tsx` | No (Wave 2) |
| NAV-02 | Breadcrumbs render Home > Search > {course} on /courses/:id | unit | `cd frontend && npx vitest run src/components/Breadcrumbs.test.tsx` | No (Wave 2) |
| NAV-02 | No breadcrumbs rendered on / (Home page) | unit | `cd frontend && npx vitest run src/components/Breadcrumbs.test.tsx` | No (Wave 2) |
| NAV-03 | Hamburger button visible on mobile | unit | `cd frontend && npx vitest run src/components/MobileMenu.test.tsx` | No (Wave 2) |
| NAV-03 | Sheet opens on hamburger click | unit | `cd frontend && npx vitest run src/components/MobileMenu.test.tsx` | No (Wave 2) |
| NAV-03 | Sheet closes after link click | unit | `cd frontend && npx vitest run src/components/MobileMenu.test.tsx` | No (Wave 2) |
| NAV-04 | App.tsx routes registered correctly | unit | `cd frontend && npx vitest run src/App.test.tsx` | No (Wave 1) |
| NAV-04 | HomePage renders at / | unit | `cd frontend && npx vitest run src/pages/HomePage.test.tsx` | No (Wave 1) |

---

## Wave 0 Gaps

All test files are created during execution (TDD approach per plan tasks).

---

*Phase: 06-navigation-routing*
*Validation strategy created: 2026-04-07*

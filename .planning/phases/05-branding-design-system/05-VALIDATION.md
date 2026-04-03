---
phase: 5
slug: branding-design-system
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-02
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest 3.2.4 |
| **Config file** | `frontend/vitest.config.ts` |
| **Quick run command** | `npm test` (from `frontend/`) |
| **Full suite command** | `npm test` (from `frontend/`) |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `npm test` (from `frontend/`)
- **After every plan wave:** Run `npm test` (from `frontend/`)
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | BRAND-01 | visual (manual) | — | N/A | ⬜ pending |
| 05-01-02 | 01 | 1 | BRAND-01 | unit (CSS token) | `npm test -- --reporter=verbose` | ❌ W0 | ⬜ pending |
| 05-02-01 | 02 | 1 | BRAND-02 | visual (manual) | — | N/A | ⬜ pending |
| 05-03-01 | 03 | 1 | BRAND-03 | unit | `npm test -- --reporter=verbose` | ❌ W0 | ⬜ pending |
| 05-03-02 | 03 | 1 | BRAND-03 | unit | `npm test -- --reporter=verbose` | ❌ W0 | ⬜ pending |
| 05-03-03 | 03 | 1 | BRAND-03 | unit | `npm test -- src/components/ProfessorCard.test.tsx` | ✅ (needs update) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/src/pages/SearchPage.test.tsx` — stubs for BRAND-03 document.title behavior for Search page
- [ ] `frontend/src/pages/CoursePage.test.tsx` — stubs for BRAND-03 document.title behavior for Course page
- [ ] Update `frontend/src/components/ProfessorCard.test.tsx` — update score assertion from plain text `'75'` to handle Badge wrapper; add test for score badge color class per banding threshold

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Token replacement propagates teal/amber to all components — no gray defaults | BRAND-01 | CSSOM not processed in happy-dom; @theme inline not evaluable in test env | Open app in browser, inspect computed styles on Card, Button, Badge — verify primary resolves to teal, accent to amber |
| Font CSS variables resolve to Poppins/Open Sans | BRAND-02 | DevTools font inspection required; happy-dom does not render fonts | Open app, inspect any heading in DevTools → Computed tab → font-family shows "Poppins Variable" |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

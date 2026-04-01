---
phase: 3
slug: react-frontend
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-01
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest 4.1.2 |
| **Config file** | `frontend/vitest.config.ts` — Wave 0 gap |
| **Quick run command** | `cd frontend && npm run test -- --run` |
| **Full suite command** | `cd frontend && npm run test` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npm run test -- --run`
- **After every plan wave:** Run `cd frontend && npm run test`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 0 | (infra) | config | `cd frontend && npm run build` | n/a | ⬜ pending |
| 03-02-01 | 02 | 1 | UI-02, UI-07 | unit + config | `cd frontend && npx tsc --noEmit` | ❌ W0 | ⬜ pending |
| 03-02-02 | 02 | 1 | UI-02, UI-07 | unit (TDD) | `vitest run src/lib/scoring.test.ts` | ❌ W0 | ⬜ pending |
| 03-03-01 | 03 | 2 | UI-01 | component | `vitest run src/components/CourseSearch.test.tsx` | ❌ W0 | ⬜ pending |
| 03-03-02 | 03 | 2 | UI-01 | component + MSW | `vitest run src/components/CourseSearch.test.tsx` | ❌ W0 | ⬜ pending |
| 03-04-01 | 04 | 2 | UI-02, UI-05, UI-08 | component | `vitest run src/components/ProfessorCard.test.tsx` | ❌ W0 | ⬜ pending |
| 03-04-02 | 04 | 2 | UI-02 | unit | `vitest run src/components/SentimentBadge.test.tsx` | ❌ W0 | ⬜ pending |
| 03-05-01 | 05 | 3 | UI-03 | component | `vitest run src/components/GradeChart.test.tsx` | ❌ W0 | ⬜ pending |
| 03-05-02 | 05 | 3 | UI-04 | component | `vitest run src/components/GpaTrendChart.test.tsx` | ❌ W0 | ⬜ pending |
| 03-06-01 | 06 | 3 | UI-07 | component | `vitest run src/components/WeightSliders.test.tsx` | ❌ W0 | ⬜ pending |
| 03-06-02 | 06 | 3 | UI-07 | unit | `vitest run src/lib/scoring.test.ts` | ❌ W0 | ⬜ pending |
| 03-07-01 | 07 | 4 | UI-10 | component | `vitest run src/components/SkeletonCard.test.tsx` | ❌ W0 | ⬜ pending |
| 03-07-02 | 07 | 4 | UI-11 | unit (timer mock) | `vitest run src/hooks/useElapsedTime.test.ts` | ❌ W0 | ⬜ pending |
| 03-07-03 | 07 | 4 | DEPLOY-01 | config check | `grep -q "/(.\*)" frontend/vercel.json && echo "PASS"` | n/a | ⬜ pending |
| 03-07-04 | 07 | 4 | UI-09 | manual (visual) | — | manual only | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/vitest.config.ts` — Vitest + jsdom config with React plugin and path aliases
- [ ] `frontend/src/test/setup.ts` — RTL cleanup + MSW server lifecycle
- [ ] `frontend/src/test/mswServer.ts` — MSW handlers for all 4 API endpoints
- [ ] `frontend/src/lib/scoring.test.ts` — stubs for UI-02, UI-07
- [ ] `frontend/src/components/SentimentBadge.test.tsx` — stubs for UI-06
- [ ] `frontend/src/hooks/useElapsedTime.test.ts` — stubs for UI-11
- [ ] Framework install: `npm install -D vitest jsdom @testing-library/react @testing-library/user-event @testing-library/jest-dom msw`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Mobile layout: cards stack full-width at < md breakpoint | UI-09 | Vitest + jsdom cannot verify CSS breakpoints or computed layout | Open browser at 375px width, verify cards are full-width and no horizontal scroll |
| Touch targets >= 44px on all interactive elements | UI-09 | jsdom cannot compute rendered element dimensions | Inspect elements in browser devtools at mobile viewport, verify min 44px height/width on buttons, sliders, toggles |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

---
phase: 4
slug: deployment
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-01
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (backend), vitest (frontend) |
| **Config file** | `pyproject.toml`, `frontend/vitest.config.ts` |
| **Quick run command** | `curl -s http://localhost:8001/health` |
| **Full suite command** | `python -m pytest test_api/ && cd frontend && npx vitest run` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `curl -s http://localhost:8001/health`
- **After every plan wave:** Run `python -m pytest test_api/ && cd frontend && npx vitest run`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | DEPLOY-01 | integration | `curl -s $VERCEL_URL` | N/A (external) | pending |
| 04-01-02 | 01 | 1 | DEPLOY-02 | integration | `curl -s -o /dev/null -w '%{http_code}' $RENDER_URL/health` | N/A (external) | pending |
| 04-02-01 | 02 | 2 | DEPLOY-02 | smoke | `curl -H 'Origin: $VERCEL_URL' $RENDER_URL/health` | N/A (external) | pending |
| 04-03-01 | 03 | 3 | DEPLOY-03 | external | UptimeRobot dashboard check | N/A (external) | pending |

*Status: pending · green · red · flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements. Deployment phase validates via external service checks, not unit tests.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| SPA deep link navigation | DEPLOY-01 | Requires live Vercel URL | Navigate to `$VERCEL_URL/courses/11082` — page loads professors |
| Cross-origin API calls | DEPLOY-02 | Requires live CORS from browser | Open browser console on Vercel URL, confirm no CORS errors |
| Cold-start recovery | DEPLOY-03 | Requires Render spin-down cycle | Wait 20 min, then load page — observe skeleton cards then data |

---

## Validation Sign-Off

- [ ] All tasks have automated verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

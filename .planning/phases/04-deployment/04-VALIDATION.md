---
phase: 4
slug: deployment
status: draft
nyquist_compliant: true
wave_0_complete: true
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
| 04-01-01 | 01 | 1 | DEPLOY-02 | unit | `pytest tests/test_config.py -x -v` | `tests/test_config.py` (created within this task via TDD Step 1) | pending |
| 04-01-02 | 01 | 1 | DEPLOY-01 | file-check | `cat .python-version && grep ALLOWED_ORIGINS .env.example && grep VITE_API_URL frontend/.env.example` | N/A (static files) | pending |
| 04-02-01 | 02 | 2 | DEPLOY-01 | smoke | `curl -s -o /dev/null -w '%{http_code}' $RENDER_URL/health` | N/A (external) | pending |
| 04-02-02 | 02 | 2 | DEPLOY-02 | smoke | `curl -H 'Origin: $VERCEL_URL' $RENDER_URL/health` | N/A (external) | pending |
| 04-02-03 | 02 | 2 | DEPLOY-03 | external | UptimeRobot dashboard check | N/A (external) | pending |

*Status: pending / green / red / flaky*

**Notes:**
- Task 04-01-01 covers DEPLOY-02 (CORS env-var configuration) with unit tests verifying the `allowed_origins` field_validator in `api/config.py`. The test file `tests/test_config.py` is created within this task as TDD Step 1 (write failing tests first, then implement).
- Task 04-01-02 covers DEPLOY-01 preparation (`.python-version` for Render, `.env.example` files for both services).
- Tasks 04-02-01 through 04-02-03 are external service verifications (Render, Vercel, UptimeRobot) that require live deployments.

---

## Wave 0 Requirements

*`tests/test_config.py` is created within 04-01 Task 1 via TDD Step 1 (write failing tests before implementation). No separate Wave 0 task is needed because the test file is authored as the first action of the task itself.*

*All other phase verifications are external service checks (live URLs, dashboard status) that have no pre-existing test dependencies.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| SPA deep link navigation | DEPLOY-01 | Requires live Vercel URL | Navigate to `$VERCEL_URL/courses/11082` — page loads professors |
| Cross-origin API calls | DEPLOY-02 | Requires live CORS from browser | Open browser console on Vercel URL, confirm no CORS errors |
| Cold-start recovery | DEPLOY-03 | Requires Render spin-down cycle | Wait 20 min, then load page — observe skeleton cards then data |

---

## Validation Sign-Off

- [x] All tasks have automated verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

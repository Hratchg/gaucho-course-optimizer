---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: UI/UX Overhaul
status: active
stopped_at: null
last_updated: "2026-04-02"
last_activity: 2026-04-02 — Milestone v1.1 started
progress:
  total_phases: 0
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-02)

**Core value:** Students can search any UCSB course and instantly see which professor will give them the best outcome — ranked by a score combining GPA, RMP quality, difficulty, and sentiment
**Current focus:** Defining requirements for v1.1 UI/UX Overhaul

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: 2026-04-02 — Milestone v1.1 started

Progress: [░░░░░░░░░░] 0%

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Pre-roadmap: Use Neon (not Render) for PostgreSQL — Render free DB expires every 30 days
- Pre-roadmap: Fix N+1 query, missing indexes, and connection pool before building API layer
- Pre-roadmap: Expose raw factor values from API so weight sliders recompute in browser without round-trips
- Phase 1: Alembic confirmed present — FK indexes applied via migration (not __table_args__)
- Phase 1: RMP auth token moved to RMP_AUTH_TOKEN env var
- Phase 1: Scoring N+1 patched with batch sessions; bulk JOIN rewrite needed before Phase 2

### Pending Todos

- Bulk JOIN rewrite of compute_all_scores() before Phase 2 API work (scoring N+1 documented in memory)

### Blockers/Concerns

- Scoring N+1 pattern (3 queries × 11,750 pairs): patched but not fully solved. Rewrite to bulk JOIN needed before Phase 2 to ensure API endpoint `GET /courses/{id}/professors` is fast.

## Session Continuity

Last session: 2026-04-02
Stopped at: Milestone v1.1 initialization
Resume file: —

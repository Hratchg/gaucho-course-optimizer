# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-30)

**Core value:** Students can search any UCSB course and instantly see which professor will give them the best outcome — ranked by a score combining GPA, RMP quality, difficulty, and sentiment
**Current focus:** Phase 1 — Foundation & Bug Fixes

## Current Position

Phase: 1 of 4 (Foundation & Bug Fixes)
Plan: 0 of ? in current phase
Status: Ready to plan
Last activity: 2026-03-30 — Roadmap created, milestone v1.0 initialized

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: -
- Total execution time: -

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**
- Last 5 plans: -
- Trend: -

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Pre-roadmap: Use Neon (not Render) for PostgreSQL — Render free DB expires every 30 days
- Pre-roadmap: Fix N+1 query, missing indexes, and connection pool before building API layer
- Pre-roadmap: Expose raw factor values from API so weight sliders recompute in browser without round-trips

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 1: Alembic migration state unknown — check for `alembic/` directory before deciding index strategy (`__table_args__` vs migration file)
- Phase 1: Hardcoded RMP auth token in `rmp_scraper.py` must be verified and migrated to env var before any pipeline run against production Neon DB

## Session Continuity

Last session: 2026-03-30
Stopped at: Roadmap created — ready to plan Phase 1
Resume file: None

---
gsd_state_version: 1.0
milestone: v2.2
milestone_name: Schedule Data Completeness
status: complete
stopped_at: Operations work (CI, scheduled jobs, production cleanup) done; see docs/handoff/2026-09-29-operations-handoff.md
last_updated: "2026-09-29"
last_activity: 2026-09-29
progress:
  total_phases: 1
  completed_phases: 1
  total_plans: 1
  completed_plans: 1
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-07)

**Core value:** Students can search any UCSB course and instantly see which professor will give them the best outcome -- ranked by a score combining GPA, RMP quality, difficulty, and sentiment
**Current focus:** Milestone v2.2 complete. Since then (2026-09-28/29): CI restored, every scheduled job on GitHub Actions, production schema at Alembic head, and production data cleaned up. Start from [docs/handoff/2026-09-29-operations-handoff.md](../docs/handoff/2026-09-29-operations-handoff.md).

## Current Position

Phase: 18 (final)
Plan: 18-01 complete
Status: Milestone v2.2 complete
Last activity: 2026-04-14

Progress: [██████████] 100% (v2.2 complete)

## Performance Metrics

**Velocity:**

- Total plans completed: 41 (v1.0: 18, v1.1: 6, v1.2: 5, v2.0: 4, v2.1: 2)
- Average duration: varies
- Total execution time: varies

## Accumulated Context

### Decisions

Recent decisions affecting current work:

- Auto-create professor records for unmatched UCSB instructors during schedule sync
- Nightly sync now covers both current AND next quarter (not just next)
- GitHub Actions cron job replaces APScheduler for production schedule sync (Render has no persistent scheduler process)
- Course-level sections panel shows only sections with named instructor + meeting time
- Auto-created professors start empty but self-enrich through existing RMP scrape and grade ingestion pipelines
- Shared auto_create_cache across departments prevents duplicate professor creation within a sync run
- Frontend rebranded to CoursePick (coursepick.app), backend on Render, frontend on Vercel

### Pending Todos

The full list, with details, is in "Start here" in docs/handoff/2026-09-29-operations-handoff.md. In short:

- Check the first scheduled runs after the cleanup: nightly sync 2026-09-30, RMP refresh 2026-10-03, quarterly grades 2026-10-25.
- Review the 24 unserved probably-wrong RMP links, and the 4 duplicate pairs pass 4 skipped.
- Delete the Neon backup branches `pre-schema-reconcile-2026-09-29` and `pre-data-cleanup-2026-09-29` after about 2026-10-06.

### Blockers/Concerns

- Render does not run `preDeployCommand`, so migrations must be applied to production by hand (docs/runbooks/reconcile-production-schema.md).
- `tests/conftest.py` drops every table at the end of a test session and reads `DATABASE_URL` from `.env`. Never run pytest with a `.env` that points at Neon.
- Grade loads can create abbreviated-name duplicate professors. Pass 4 (the "Enhanced professor matching" workflow) cleans them up, but only when run by hand.

## Session Continuity

Last session: 2026-09-29
Stopped at: Operations handoff written; no work in progress
Resume file: docs/handoff/2026-09-29-operations-handoff.md

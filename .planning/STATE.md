---
gsd_state_version: 1.0
milestone: v2.2
milestone_name: Schedule Data Completeness
status: complete
stopped_at: Open-items spec worked through; #19-#21 merged and the 2026-09-30 production cleanup done; see docs/handoff/2026-09-29-evening-operations-handoff.md
last_updated: "2026-09-30"
last_activity: 2026-09-30
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
**Current focus:** Milestone v2.2 complete. Since then (2026-09-28/29): CI restored, every scheduled job on GitHub Actions, production schema at Alembic head, and production data cleaned up. The follow-up session fixed the test-suite guard (#17), the grade loader (#18), the sync misattribution (#19) and added a migration drift check (#20). On 2026-09-30 it removed the 1,476 same-name duplicate professors (#21), re-pointed past-quarter sections with the new matcher, and merged WOODS. Start from [docs/handoff/2026-09-29-evening-operations-handoff.md](../docs/handoff/2026-09-29-evening-operations-handoff.md).

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

The full list, with details, is in "Open items, in order" in docs/handoff/2026-09-29-evening-operations-handoff.md. In short:

- Check the scheduled runs:
  - nightly sync 2026-10-01: after #19's first run on 2026-09-30 (72 professors created, checked), expect only a handful;
  - RMP refresh 2026-10-03;
  - backup 2026-10-04;
  - quarterly grades 2026-10-25.
- Review the 24 probably-wrong RMP links (needs `RMP_AUTH_TOKEN`), after the 2026-10-03 refresh.
- At the 2026-10-25 grade load, confirm B6's fix (#23): no grades copied onto sync-created short names.
- Review the pass 4 pair `YIN Y` → `YIN YOUWEI` before anyone dispatches "Enhanced professor matching".
- Fix the schedule sync for multi-word department codes (POL S, CH E, RG ST, ...), which have never had sections.
- Delete the Neon backup branches from about 2026-10-06 (2026-09-29 backups) and 2026-10-07 (2026-09-30 backups).

### Blockers/Concerns

- Render does not run `preDeployCommand`, so migrations must be applied to production by hand (docs/runbooks/reconcile-production-schema.md). The daily drift check (#20) opens a `migration-drift` issue when one is pending.
- The GitHub `*/15` uptime schedule actually runs every 4-6 hours, so an outage can go unnoticed for hours.

## Session Continuity

Last session: 2026-09-30
Stopped at: #19-#21 merged, production cleanup done and verified, no work in progress
Resume file: docs/handoff/2026-09-29-evening-operations-handoff.md

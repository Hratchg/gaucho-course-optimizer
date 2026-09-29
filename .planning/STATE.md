---
gsd_state_version: 1.0
milestone: v2.2
milestone_name: Schedule Data Completeness
status: complete
stopped_at: Open-items spec worked through; PRs #19-#21 await a merge decision; see docs/handoff/2026-09-29-evening-operations-handoff.md
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
**Current focus:** Milestone v2.2 complete. Since then (2026-09-28/29): CI restored, every scheduled job on GitHub Actions, production schema at Alembic head, and production data cleaned up. The follow-up session fixed the test-suite guard (#17) and the grade loader (#18), and opened #19 (sync misattribution), #20 (migration drift check) and #21 (same-name duplicates plan). Start from [docs/handoff/2026-09-29-evening-operations-handoff.md](../docs/handoff/2026-09-29-evening-operations-handoff.md).

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

- Decide on PRs #19 (merging it changes production data at the next nightly), #20 and #21.
- Check the scheduled runs: nightly sync 2026-09-30, RMP refresh 2026-10-03, backup 2026-10-04, quarterly grades 2026-10-25.
- Review the 24 probably-wrong RMP links (needs `RMP_AUTH_TOKEN`), after the 2026-10-03 refresh.
- After #19: re-point past-quarter sections (20262/20263) with the new matcher. Run the #21 plan, then the WOODS merge.
- Fix the schedule sync for multi-word department codes (POL S, CH E, RG ST, ...), which have never had sections.
- Delete the Neon backup and rehearsal branches after about 2026-10-06.

### Blockers/Concerns

- Render does not run `preDeployCommand`, so migrations must be applied to production by hand (docs/runbooks/reconcile-production-schema.md). Once #20 merges, a `migration-drift` issue flags a pending migration.
- The nightly sync attaches some sections to the wrong professor until #19 merges, and past quarters stay wrong until they're re-pointed.
- The GitHub `*/15` uptime schedule actually runs every 4-6 hours, so an outage can go unnoticed for hours.

## Session Continuity

Last session: 2026-09-29
Stopped at: Evening operations handoff written; PRs #19-#21 open, no work in progress
Resume file: docs/handoff/2026-09-29-evening-operations-handoff.md

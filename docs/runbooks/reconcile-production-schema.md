# Runbook: reconcile the production schema with Alembic

**Applies to:** Neon project `ancient-river-48578866`, branch `production` (`br-steep-hill-akgx2zmo`), database `neondb`.
**Target revision:** `9acf49a4b131` (head as of 2026-09-29).
**Expected duration:** about 3 seconds of migration time. Writes to five tables are blocked for about 1.6 s, and reads of `gaucho_scores` for about 0.1 s.
**Status:** applied to production on 2026-09-29. Production is at `9acf49a4b131`, and `compare_metadata` returns `[]`. Keep this runbook for the next migration: Render still doesn't run them (section 6). See [the 2026-09-29 handoff](../handoff/2026-09-29-operations-handoff.md).

## Why this is needed

Production was stamped at the initial revision `3ee0c9e2add3` and never migrated again:

| Object | Models | `upgrade head` before 9acf49a4b131 | Production before the fix |
|---|---|---|---|
| `alembic_version` | n/a | `c4a8e1b0f2d3` | `3ee0c9e2add3` |
| `scheduled_sections` table | yes | created by `c4a8e1b0f2d3` | yes, identical columns, FKs and unique constraint (built with `create_all`, see `.planning/phases/16-*/16-01-SUMMARY.md`) |
| `ix_grade_distributions_professor_id`, `ix_grade_distributions_course_id`, `ix_rmp_ratings_professor_id`, `ix_rmp_comments_rmp_rating_id`, `ix_gaucho_scores_professor_id`, `ix_gaucho_scores_course_id` | no (added in this PR) | yes (`1fd97b94581d`) | **missing** |
| `ix_scheduled_sections_professor_id`, `_course_id`, `_quarter_code` | no (added in this PR) | yes (`c4a8e1b0f2d3`) | **missing** |
| `uq_gaucho_score_pair UNIQUE (professor_id, course_id)` on `gaucho_scores` | yes | **no** | **missing** |

Every column name, type, nullability, server default (none except the `id` sequences), foreign key and the other unique constraints already match. Nothing exists in production that the migrations lack.

## Why a plain `alembic upgrade head` (no `stamp`)

The migrations after `3ee0c9e2add3` are already idempotent against production's state:

* `1fd97b94581d` uses `CREATE INDEX IF NOT EXISTS`.
* `c4a8e1b0f2d3` skips `CREATE TABLE scheduled_sections` when the table exists, and creates only the indexes that are missing.
* `9acf49a4b131` (new) adds `uq_gaucho_score_pair`. It does nothing if the constraint is already there, adopts a hand-built unique index of that name if one exists, and raises an error that lists the duplicate pairs if any exist.

So the owner doesn't need to run `alembic stamp` by hand. Stamping would also be risky: if Render's `preDeployCommand` ever runs, it runs `alembic upgrade head` from whatever revision is stamped, so the chain has to be safe from `3ee0c9e2add3` anyway. That path was rehearsed on a Neon branch (see "Rehearsal" below).

On PostgreSQL, Alembic runs the whole upgrade in **one transaction**, so the run is all-or-nothing. If the duplicate check or a lock timeout fails the run, the indexes from the earlier revisions roll back too. `db/migrations/env.py` sets `lock_timeout` (default `5s`, override with `ALEMBIC_LOCK_TIMEOUT`). A migration that can't get its lock fails quickly instead of queueing, which would stall the API's reads behind it.

`CREATE INDEX CONCURRENTLY` isn't used. The largest table is `grade_distributions` (about 106k rows, 14 MB), and each index builds in about 50 to 170 ms including network round trip. `CONCURRENTLY` can't run inside a transaction: Alembic would need `op.get_context().autocommit_block()`, which loses the all-or-nothing rollback above, and a failed concurrent build leaves an `INVALID` index behind that needs manual cleanup. Consider it only once a table grows past a few million rows.

## 0. Prerequisites

* A checkout of `master` with this PR merged, and `pip install -r requirements-api.txt` (or `requirements-dev.txt`).
* The production connection string. Prefer the **direct** (non `-pooler`) host for DDL. The pooled host also works: it was used in the rehearsal.
  Don't paste it into files or shell history: `read -rs DATABASE_URL && export DATABASE_URL`.

## 1. Back up first

Do either one. Both is better.

* **Neon branch (instant, recommended):** Neon console, project `ancient-river-48578866`, Branches, New branch from `production`, name it `pre-schema-reconcile-YYYY-MM-DD`. Or use the CLI: `neonctl branches create --project-id ancient-river-48578866 --parent production --name pre-schema-reconcile-$(date +%F)`.
* **pg_dump artifact:** GitHub, Actions, **Weekly Neon DB Backup**, Run workflow on `master`. Or use the CLI: `gh workflow run weekly-pgdump.yml --ref master && gh run watch`. Check that the run is green and the `neon-backup-<run_id>` artifact exists.

## 2. Preflight (read only)

```sql
SELECT version_num FROM alembic_version;                        -- expect 3ee0c9e2add3
SELECT count(*) FROM gaucho_scores;                             -- ~11.8k at time of writing
SELECT professor_id, course_id, count(*) FROM gaucho_scores
GROUP BY 1, 2 HAVING count(*) > 1;                              -- expect 0 rows
SELECT pid, state, xact_start, left(query, 80) FROM pg_stat_activity
WHERE datname = current_database() AND xact_start < now() - interval '5 seconds';
                                                                -- long transactions will trip lock_timeout
```

If the duplicate query returns rows, the migration refuses to run. Keep the newest row per pair, but only after the backup:

```sql
DELETE FROM gaucho_scores g USING gaucho_scores newer
WHERE g.professor_id = newer.professor_id AND g.course_id = newer.course_id
  AND (newer.computed_at, newer.id) > (g.computed_at, g.id);
```

(`gaucho_scores` is a derived cache that the weekly RMP refresh rewrites, and the API doesn't read it. See `scheduler/jobs.py`.)

Avoid running this while the weekly RMP refresh or the nightly schedule sync is running (see `.github/workflows/`).

## 3. Apply

```bash
alembic current            # expect: 3ee0c9e2add3
alembic upgrade head       # 3ee0c9e2add3 -> 1fd97b94581d -> c4a8e1b0f2d3 -> 9acf49a4b131
alembic current            # expect: 9acf49a4b131 (head)
alembic upgrade head       # expect: no "Running upgrade" lines (no-op)
```

If this PR is deployed by a Render service that does run `preDeployCommand`, step 3 happens on merge automatically. It's the same command, so it's equally safe. Run step 1 **before merging** in that case.

## 4. Verify

```sql
SELECT version_num FROM alembic_version;                                      -- 9acf49a4b131
SELECT indexname FROM pg_indexes WHERE schemaname = 'public' AND indexname LIKE 'ix\_%' ORDER BY 1;  -- 9 rows
SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = 'uq_gaucho_score_pair';
                                                                              -- UNIQUE (professor_id, course_id)
SELECT count(*) FROM gaucho_scores;                                           -- unchanged from preflight
```

Check that the models match the live schema (this should print `[]`):

```bash
python -c "
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from db.connection import get_engine
from db.models import Base
with get_engine().connect() as c: print(compare_metadata(MigrationContext.configure(c), Base.metadata))"
```

Smoke-test the API: `curl -s -o /dev/null -w '%{http_code}\n' https://gaucho-course-optimizer.onrender.com/ready` should print 200, and so should `/courses/<id>/professors` for a known course.

## 5. Rollback

* **Constraint only:** `alembic downgrade c4a8e1b0f2d3` runs `DROP CONSTRAINT IF EXISTS uq_gaucho_score_pair`. It takes about 0.4 s and touches no data.
* **Indexes:** they only speed up reads and there's no reason to remove them. If one causes a problem, `DROP INDEX CONCURRENTLY ix_...` it individually and leave the revision alone.
* **Do not** `alembic downgrade` below `c4a8e1b0f2d3` in production. That revision's downgrade drops the `scheduled_sections` table and its data.
* **Full restore:** in the Neon console, restore `production` from the `pre-schema-reconcile-*` branch (Branches, Restore), or load the pg_dump artifact with `psql "$DATABASE_URL" < gco_dump.sql`.

## 6. Make future deploys run migrations (Render)

Migrations never ran because the Render web service doesn't execute `render.yaml`. From the repo:

* `render.yaml` (with `preDeployCommand: alembic upgrade head`) was only added on 2026-09-20 in `c0cadb4`. The API was already live on `gaucho-course-optimizer.onrender.com` before that (the 2026-09-19 audit tested it), and `.planning/research/STACK.md` documents a service configured by hand in the dashboard. A dashboard-created service ignores `render.yaml` unless it's attached to a **Blueprint**.
* The project runs on Render's **free** tier (`.planning/PROJECT.md`: "Free hosting only (Vercel + Render free tiers)"; the audit also calls it a free-tier instance). **Render only runs pre-deploy commands on paid instance types**, so a free service skips them even if a Blueprint manages it. `plan: starter` in `render.yaml` is paid, so syncing the Blueprint would also change billing.
* The table that did get built, `scheduled_sections`, was created with `Base.metadata.create_all` (per the Phase 16 summary). `create_all` skips existing tables, which is why `gaucho_scores` never gained `uq_gaucho_score_pair`.

Check in the Render dashboard:

1. **Service, Settings, Instance Type.** If it's Free, `preDeployCommand` won't run. Either upgrade to Starter or later, or keep running step 3 by hand after each merge that adds a migration.
2. **Service, Settings, Build & Deploy, Pre-Deploy Command.** It should read `alembic upgrade head`. If it's blank, the service isn't reading `render.yaml`.
3. **Blueprints page.** Is `gaucho-course-optimizer` listed and linked to this repo's `render.yaml`, with the last sync succeeding? If not, either create a Blueprint instance from the repo (this adopts the existing service by name) or set the Pre-Deploy Command in the dashboard by hand.
4. **Service, Environment.** `DATABASE_URL` must point at the Neon `production` branch. For migrations, the direct host is preferred over `-pooler`.
5. **Events / Deploy logs of the next deploy.** Confirm a "Pre-deploy" step ran and printed `Running upgrade ...` or nothing (already at head). If a pre-deploy fails, Render keeps the previous release live.

## Guardrail against future drift

`tests/test_migrations.py` runs in CI (`.github/workflows/test.yml`). On a scratch database it:

* upgrades a fresh database to head and asserts `compare_metadata(models)` is empty, so a model change without a migration fails CI;
* checks that a second `upgrade head` is a no-op;
* reproduces production's exact pre-fix state (stamped `3ee0c9e2add3` with a hand-built `scheduled_sections`), upgrades it, and asserts the result matches the models;
* checks that duplicate score pairs make the upgrade fail with nothing changed, and that downgrade/re-upgrade and adopting a hand-built index both work.

When you change `db/models.py`, generate the migration with `alembic revision --autogenerate -m "..."` and review it.

CI only proves the migrations are right; it doesn't apply them. `.github/workflows/migration-drift.yml` watches production itself. It runs daily at 20:00 UTC, on every push to master that touches `db/migrations/**` or `db/models.py`, and by hand. It runs `scripts/check_migration_drift.py` read-only against the `DATABASE_URL` secret, and flags drift in two cases:

* `alembic_version` isn't the repo head, whether behind or at a revision the repo doesn't have;
* `compare_metadata` isn't empty.

It tracks drift in one `migration-drift` issue, which lists the pending revisions and schema differences. The issue closes itself once production is in sync. So after merging a migration, expect that issue to open, and apply the migration with steps 1 to 4 above. To check by hand:

```bash
DATABASE_URL=... python scripts/check_migration_drift.py   # exit 0 in sync, 1 drift, 2 couldn't check
```

## Rehearsal (2026-09-29)

On Neon branch `fix-schema-drift-dry-run` (`br-wandering-cloud-akweblcq`), branched from `production` at LSN `0/21EF15B8`:

* `alembic current` showed `3ee0c9e2add3`. `alembic upgrade head` ran through all three revisions. The transaction was open for 1.62 s (2.56 s wall clock over the internet), and each statement took 40 to 175 ms, of which about 40 ms is network round trip.
* `alembic current` then showed `9acf49a4b131 (head)`. A second `upgrade head` ran no revisions.
* The branch's `pg_dump --schema-only` was identical to a fresh `upgrade head` database, and `compare_metadata` returned `[]`.
* Row counts didn't change (11,779 scores, 12,409 sections, 105,864 grade rows).
* The full backend suite (288 tests) passed against a scratch database on the branch's PG 17 compute.
* `uvicorn api.main:app` against the branch returned 200 for `/ready` and for `/courses/11082/professors` (27 professors).
* `downgrade -1` followed by `upgrade head` round-tripped cleanly.
* Holding a read lock on `gaucho_scores` from another session made the migration fail with `LockNotAvailable` after 5 s, leaving the database unchanged.

# Runbook: delete orphan professor rows

One-off cleanup of the duplicate `professors` rows the nightly schedule sync
created before PR #1 (commit 4337c14). The script is
`scripts/delete_orphan_professors.py`. It is dry-run by default.

## What gets deleted

A row is deleted only if all of these hold:

- no row in `grade_distributions`, `rmp_ratings`, `gaucho_scores` or
  `scheduled_sections` has its id (these are the only columns that hold a
  `professors.id`; the script aborts if it finds another foreign key to
  `professors`);
- `rmp_id` and `name_rmp` are both NULL;
- an older row (lower id) with the same `name_nexus` exists.

So the oldest row of every name is always kept, and rows with a NULL
`name_nexus` are never touched. The schedule sync and the grades loader both
resolve a name to the oldest matching row, so they pick the same id after the
cleanup as before it.

Rehearsal on a copy of production (Neon branch `cleanup-orphans-dry-run`,
2026-09-28): 84,034 of 92,687 rows deleted, 8,653 left.

## 1. Pick a time

Don't overlap a job that writes professors or references to them:

| Job | When (UTC) |
| --- | --- |
| Nightly Schedule Sync | daily 08:30 |
| Weekly Neon DB Backup | Sunday 06:00 |
| Weekly RMP refresh | Saturday 09:00 |
| Quarterly grades | 25 Jan/Apr/Jul/Oct 10:00 |

Overlap would not corrupt anything (each batch re-checks references under row
locks, and the foreign keys reject a bad delete), but a quiet window keeps the
counts easy to verify.

## 2. Back up

Do both; they are cheap.

1. Dispatch the "Weekly Neon DB Backup" workflow and wait for it to finish:

   ```sh
   gh workflow run weekly-pgdump.yml --ref master
   gh run watch "$(gh run list --workflow weekly-pgdump.yml --limit 1 --json databaseId -q '.[0].databaseId')"
   ```

   The dump is uploaded as the `neon-backup-<run id>` artifact (kept 90 days).

2. Create a Neon branch from `main` named e.g. `pre-orphan-cleanup-YYYYMMDD`
   (console: Branches, New branch; or `neonctl branches create --name ...`).
   This is the fastest rollback path. Keep it until you are satisfied.

## 3. Pre-check

With `DATABASE_URL` pointing at production (the script prints the target host
before doing anything, so check it):

```sh
python scripts/delete_orphan_professors.py
```

Confirm:

- "deletable orphan rows" is around 84,000 (it may drift by a few as the sync
  runs; a jump means something changed, so stop and investigate);
- the most-duplicated names and the random sample look like sync leftovers
  (upper-case `LAST F M` names, many copies).

The dry run takes a few seconds.

## 4. Run

```sh
python scripts/delete_orphan_professors.py --apply
```

It deletes 5,000 rows per transaction (`--batch-size` to change) and logs each
batch. The rehearsal took about 10 minutes: 17 batches of about 35 seconds
each. Most of that is Postgres checking each foreign key by scanning the
referencing tables, because production has no index on the `professor_id`
columns (see the note below). If it is interrupted, the batches already
committed stay deleted; just run it again. A second run deletes nothing.

Only the rows being deleted are locked, and nothing references them, so the
site and the other jobs keep working while it runs.

Note: production's `alembic_version` is still `3ee0c9e2add3` (the initial
schema), and the `ix_*_professor_id` indexes from `1fd97b94581d` and
`c4a8e1b0f2d3` do not exist there. The cleanup doesn't need them, but
`alembic upgrade head` beforehand would make the batches much faster. That is
a separate change; decide on it on its own.

## 5. Verify

```sql
-- Row counts: professors drops by the deleted count, the rest are unchanged
-- (compare with the numbers the dry run printed).
SELECT (SELECT count(*) FROM professors)          AS professors,
       (SELECT count(DISTINCT name_nexus) FROM professors) AS distinct_names,
       (SELECT count(*) FROM grade_distributions) AS grades,
       (SELECT count(*) FROM scheduled_sections)  AS sections,
       (SELECT count(*) FROM rmp_ratings)         AS ratings,
       (SELECT count(*) FROM gaucho_scores)       AS scores;

-- No dangling references (all four should be 0).
SELECT 'grade_distributions', count(*) FROM grade_distributions g
  WHERE NOT EXISTS (SELECT 1 FROM professors p WHERE p.id = g.professor_id)
UNION ALL SELECT 'rmp_ratings', count(*) FROM rmp_ratings r
  WHERE NOT EXISTS (SELECT 1 FROM professors p WHERE p.id = r.professor_id)
UNION ALL SELECT 'gaucho_scores', count(*) FROM gaucho_scores s
  WHERE NOT EXISTS (SELECT 1 FROM professors p WHERE p.id = s.professor_id)
UNION ALL SELECT 'scheduled_sections', count(*) FROM scheduled_sections s
  WHERE s.professor_id IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM professors p WHERE p.id = s.professor_id);

-- Nothing left to delete (should be 0), and no name has more than a few
-- copies left (the oldest plus copies that old sections still point at).
SELECT (SELECT count(*) FROM professors p
         WHERE p.rmp_id IS NULL AND p.name_rmp IS NULL
           AND NOT EXISTS (SELECT 1 FROM grade_distributions r WHERE r.professor_id = p.id)
           AND NOT EXISTS (SELECT 1 FROM rmp_ratings r WHERE r.professor_id = p.id)
           AND NOT EXISTS (SELECT 1 FROM gaucho_scores r WHERE r.professor_id = p.id)
           AND NOT EXISTS (SELECT 1 FROM scheduled_sections r WHERE r.professor_id = p.id)
           AND EXISTS (SELECT 1 FROM professors k
                        WHERE k.name_nexus = p.name_nexus AND k.id < p.id)) AS still_deletable,
       (SELECT max(n) FROM (SELECT count(*) AS n FROM professors
                            WHERE name_nexus IS NOT NULL GROUP BY name_nexus) d) AS max_copies;
```

`distinct_names` must be the same as before the run: every name keeps its
oldest row. In the rehearsal: professors 92,687 to 8,653, distinct names 6,829
both times, grades/sections/ratings/scores unchanged, no dangling references,
`still_deletable` 0, `max_copies` 3.

The table keeps its disk pages until autovacuum reclaims them. It is small
(about 7.5 MB), so there is no need for `VACUUM FULL`; `VACUUM ANALYZE
professors;` refreshes planner statistics right away if you want.

Then:

- `curl https://<api host>/ready` returns 200, and a course's professor list
  (`/courses/<id>/professors`) looks the same as before;
- the next Nightly Schedule Sync run logs a normal `auto-created` count (a
  handful per department at most, not hundreds).

## 6. Rollback

The deleted rows had no references, so putting them back changes nothing
else. Copy them back rather than restoring the whole database, so that any
sync writes made since the backup are kept.

1. Export the professors from the backup: the `pre-orphan-cleanup-YYYYMMDD`
   Neon branch, or a scratch database loaded from the pg_dump artifact with
   `scripts/import_db.sh`.

   ```sh
   psql "$BACKUP_URL" -c "\copy professors TO 'professors_backup.csv' CSV"
   ```

2. Insert the missing rows into production (ids are restored as they were;
   the id sequence is already past them):

   ```sh
   psql "$DATABASE_URL" <<'SQL'
   BEGIN;
   CREATE TEMP TABLE professors_backup (LIKE professors);
   \copy professors_backup FROM 'professors_backup.csv' CSV
   INSERT INTO professors
   SELECT b.* FROM professors_backup b
   WHERE NOT EXISTS (SELECT 1 FROM professors p WHERE p.id = b.id);
   COMMIT;
   SQL
   ```

If you need the whole database back for some other reason, restore `main` from
the backup branch in the Neon console. That also discards everything written
since the backup.

Never load the pg_dump file straight into production: it starts with
`DROP ... IF EXISTS` for every table.

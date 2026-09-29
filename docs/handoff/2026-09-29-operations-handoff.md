# Operations handoff, 2026-09-29

Start here when you pick the project back up. This covers the 2026-09-28 and
2026-09-29 sessions, which:

- restored CI;
- moved every scheduled job to GitHub Actions;
- brought the production schema up to Alembic head;
- cleaned up production data.

Everything below was checked at the end of 2026-09-29.

## Where things stand

- **master** is green: the Tests workflow runs on every push and PR to master.
- **API:** `https://gaucho-course-optimizer.onrender.com`, where `/ready` returns 200. The frontend is on Vercel (coursepick.app).
- **Database:**
  - Neon project `ancient-river-48578866`, branch `production` (`br-steep-hill-akgx2zmo`), Postgres 17.
  - The schema is at Alembic head `9acf49a4b131`, and `compare_metadata` against `db/models.py` returns `[]` (no drift).
- **No open PRs or issues.**

Production row counts at the end of the session:

| | count |
|---|---:|
| professors | 8,620 (6,799 distinct Nexus names) |
| Nexus professors linked to RMP | 926 (153 at confidence 85 or above, the serve-time threshold) |
| RMP-only rows | 343 |
| grade_distributions | 105,732 (latest year 2026) |
| scheduled_sections | 12,439 (quarters 20262, 20263, 20264) |
| rmp_ratings / rmp_comments | 1,581 / 13,858 |
| gaucho_scores | 10,962 |

## Start here: open items, in order

To hand these to an agent, point it at
[docs/prompts/2026-09-29-open-items-spec.md](../prompts/2026-09-29-open-items-spec.md). That
spec turns each item into a task, with safety rules and approval gates.

1. **Check the first scheduled runs after the cleanup** (GitHub, Actions tab):
   - **Nightly Schedule Sync, 2026-09-30 08:30 UTC.**
     - This is the first run with #10. The next quarter (20271) should be skipped until UCSB publishes it, instead of failing with about 95 UCSB API 400s.
     - The `auto_created` count should be a handful at most. Hundreds would mean the orphan-professor bug is back.
   - **Weekly RMP Refresh, Saturday 2026-10-03 09:00 UTC.** This is the first run after the unlink. The 100 professors that were unlinked have no ratings left, so they get searched again. Check that:
     - the freed profiles went to their likely owners from the audit:

       | professor | should get RMP profile |
       |---|---|
       | HARMON C J (5630) | 1406150 |
       | YANG T (6246) | 845193 |
       | YANG XU (7277) | 1860302 |
       | CHANG SHIYU (10165) | 2940701 |
       | SWEENEY E (10828) | 3049038 |
     - the "already linked" refusals drop from the 13 seen on 2026-09-28;
     - THOMAS C T and ALEXANDER A S did not relink to "Thomas Pettus" or "Alexander Swan". The given-name guard lets those two through (see the audit), so unlink them again if they did.

     The same run also recomputes the Gaucho Scores for the 33 professors that absorbed a merge.
   - **Weekly Neon DB Backup, Sunday 2026-10-04 06:00 UTC.**
   - **Quarterly Grades Update, 2026-10-25 10:00 UTC.** See the note on duplicate professors below.
2. **Stop the test suite from being able to wipe a real database.**
   - `tests/conftest.py` loads `DATABASE_URL` from `.env`, and its session fixture ends with `Base.metadata.drop_all()`. `.env.example` is a Neon URL template.
   - So running a bare `pytest` with a production `.env` would drop every production table. No local `.env` points at Neon today.
   - Suggested fix: make conftest refuse any host that isn't localhost, unless a flag such as `ALLOW_REMOTE_TEST_DB=1` is set.
3. **Render does not run migrations on deploy.** `preDeployCommand` in `render.yaml` never ran, so the production schema sat at `3ee0c9e2add3` until 2026-09-29.
   - To find out why, work through the dashboard checklist in [the schema runbook, section 6](../runbooks/reconcile-production-schema.md#6-make-future-deploys-run-migrations-render). The likely causes are a free instance, or a service that isn't attached to the Blueprint.
   - Until that's fixed, after merging any PR that adds a migration, apply it by hand with that runbook.
4. **Duplicate professors from grade loads.**
   - The 33 rows merged on 2026-09-29 (ids 101039 to 101075) were created by the 2026-09-28 Winter/Spring 2026 load. The 2026 CSV gives some instructors fewer initials than older data (`FAVERTY P` versus `FAVERTY P W`). The loader matches names exactly, so it created a new professor and copied that instructor's history onto it: 132 of the merged rows' grade rows were exact duplicates.
   - Pass 4 cleans this up, but it only runs by hand.
   - After each quarterly load:
     1. rehearse the "Enhanced professor matching" workflow's code on a Neon branch (see "Working safely" below);
     2. review the merges it logs;
     3. then run the workflow.
   - A longer-term fix is to make the loader match an abbreviated name to an existing full-name row in the same department.
5. **24 probably-wrong RMP links are still attached.**
   - They're listed in `docs/audits/2026-09-29-rmp-links-probably-wrong.txt`. Of that file's 31 lines, the 7 links that were showing on the site have been handled (see below); the other 24 are below confidence 85, so the site doesn't show them.
   - Review them the same way: compare the RMP profile's department and reviewed course codes with the professor's Nexus department and courses. Then run `scripts/unlink_rmp.py` on the wrong ones, as a dry run first.
   - To look up a profile, query RMP's GraphQL with `node(id: base64("Teacher-<rmp_id>"))`.
6. **4 duplicate pairs that pass 4 skipped on purpose:**

   | row left alone | reason | would merge into |
   |---|---|---|
   | RAVEN M (101052) | its grades conflict | RAVEN M A (7491, MCDB) |
   | 101060 | ambiguous: matches 2 rows | KOTH M K |
   | 101066 | ambiguous: matches 2 rows | WOODS M J or WOODS M P |
   | 101067 | ambiguous: matches 2 rows | BUENO CACHADI |

   Merge them by hand only if you can tell who is who.
7. **Delete the two backup branches after about 2026-10-06** if nothing has gone wrong (see "Backups" below).

## Scheduled jobs

All of them run on GitHub Actions. `scheduler/jobs.py` holds the job bodies; the APScheduler setup in the same file is only for local runs.

| Workflow file | When (UTC) | What it does | Secrets |
|---|---|---|---|
| `schedule-sync.yml` | daily 08:30 | UCSB schedule for the current and next quarter. Skips the next quarter until it is published. | `DATABASE_URL`, `UCSB_API_KEY` |
| `weekly-rmp-refresh.yml` | Saturday 09:00 | RMP scrape of active professors, enhanced matching passes 1-3 (no merges), NLP, scores. 300-minute timeout. Fails after 10 consecutive RMP search errors. | `DATABASE_URL`, `RMP_AUTH_TOKEN` |
| `weekly-pgdump.yml` | Sunday 06:00 | `pg_dump` saved as the `neon-backup-<run id>` artifact, kept 90 days | `DATABASE_URL` |
| `quarterly-grades.yml` | 25 Jan/Apr/Jul/Oct, 10:00 | Daily Nexus grades CSV load | `DATABASE_URL` |
| `uptime.yml` | every 15 minutes | Pings `/ready` up to 3 times. After 3 failures it opens or refreshes one issue labelled `uptime`, which closes itself once the check passes. | none |
| `enhanced-match.yml` | manual only | All four matching passes, **including pass 4 merges, which delete rows** | `DATABASE_URL` |
| `test.yml` | push and PR to master | Backend: pytest on Postgres 16. Frontend: lint, `tsc -b`, Vitest. | none |

## What changed: PRs #4 to #14

- **#4:** restored CI and the nightly sync on SQLAlchemy 2.1. It now uses `psycopg[binary]` 3, which is the driver SQLAlchemy 2.1 picks for `postgresql://`. It also added the weekly RMP refresh workflow and fixed a flaky CoursePage test by deriving the quarter filter during render.
- **#5:** moved every workflow action to its Node 24 major version.
- **#7:** the weekly refresh now links new RMP matches (passes 1 to 3). Merging duplicate professors stays manual.
- **#8:** the uptime check keeps one tracking issue instead of failing a job every 15 minutes.
- **#9:** added the quarterly grades workflow. The loader preloads existing rows, so a load takes 3 queries instead of about 3 per row. The ingester now strips the trailing spaces the 2026 CSV adds to instructor names.
- **#10:** the nightly sync skips the next quarter until UCSB publishes it.
- **#11:** pass 4 merges move every reference (grades, scores, sections, ratings), and a failed merge rolls back only that pair. The test fixtures use the SQLAlchemy 2 savepoint recipe.
- **#12:**
  - the RMP link audit (`docs/audits/2026-09-29-rmp-link-audit.md`);
  - a `given_name_conflict` guard in the scraper and in pass 2;
  - `scripts/unlink_rmp.py`.
- **#13:** `scripts/delete_orphan_professors.py`, with its runbook.
- **#14:**
  - migration `9acf49a4b131`, which adds `uq_gaucho_score_pair`;
  - a 5 s lock timeout for migrations;
  - `tests/test_migrations.py`, which fails CI when the models and the migrations drift apart;
  - the schema runbook.

## Production changes made by hand

On 2026-09-28:

- **RMP refresh:** searched 2,288 professors, linked 136, and refused 13 because the profile was already taken. The refusals led to the audit.
- **Winter and Spring 2026 grades load:** 2,594 rows.

On 2026-09-29, in this order:

1. **Schema.** `alembic upgrade head` took production from `3ee0c9e2add3` to `9acf49a4b131`. That added:
   - 9 `ix_*` indexes;
   - `uq_gaucho_score_pair`.

   All 11,779 scores were unchanged.
2. **RMP unlink, 100 professors.** This was the 96 clearly-wrong links from the audit, plus 4 of the 7 probably-wrong links that were showing on the site. It deleted 119 ratings, 1,295 comments and 817 scores. The 7 were decided by comparing each RMP profile's department and reviewed courses with the professor's own:

   | id | Nexus name (dept) | RMP profile | decision |
   |---:|---|---|---|
   | 5540 | ZIMMERMAN E D (ENV) | Don Zimmerman, Sociology, 0 ratings | unlinked |
   | 6618 | CHEN J (MATH) | Chen Ji, Geology, EARTH courses | unlinked |
   | 10865 | WALKER Z (CMPSC) | "DR Walker", Writing | unlinked |
   | 11029 | XIAO L (PSTATW) | Xiao Luo, Physics, PHYS courses | unlinked |
   | 5787 | MULFINGER J (ARTST) | ". Mulfinger", Fine Arts, ART7C | kept |
   | 9905 | TARIKERE ASHO (MATH) | Ashwin Tarikere, Mathematics, MATH3A/6A | kept |
   | 10360 | BARACALDO LAN (PSTAT) | Laura Baracaldo, Statistics, PSTAT126/134 | kept |

3. **Orphan professors.** 84,034 rows deleted: professors went from 92,690 to 8,656, and every distinct name kept its oldest row. It took 15 s now that the indexes exist; the rehearsal took about 10 minutes without them.
4. **Enhanced matching**, using the workflow (run 36611045061) after a rehearsal on a Neon branch that gave identical results:
   - 3 new links: MORGAN M (5154) to Michael Morgan, ZHANG J (10586) to Jinglan Zhang, WANG E (101083) to Eric Wang.
   - Pass 4 merged 33 duplicate pairs. 4 grade rows moved and 132 duplicate grade rows were dropped.

## Backups and rollback

| What | Where | Notes |
|---|---|---|
| Neon branch `pre-schema-reconcile-2026-09-29` | `br-late-dew-akbqg144` | Production just before the migration. Delete after about 2026-10-06. |
| Neon branch `pre-data-cleanup-2026-09-29` | `br-restless-cloud-ak2ucy84` | Production just before the unlink, the orphan delete and the merges. Delete after about 2026-10-06. |
| pg_dump artifact `neon-backup-36607600841` | Actions run 36607600841 | Taken before the migration. Kept until about 2026-12-28. |

Rollback steps are in each runbook. Never load a pg_dump file straight into production: it starts with `DROP ... IF EXISTS` for every table.

## Working safely

- **Rehearse on a Neon branch first.** Branches are instant copy-on-write copies of `production`. Run the script there, check the numbers, then run it for real. Take a backup branch just before any production data change.
- **Use the direct host** (the hostname without `-pooler`) for migrations and long scripts.
- **Keep connection strings in environment variables only.** Never put one in a committed file, and delete any temporary file that holds one.
- **The data scripts are dry runs by default.** `unlink_rmp.py` and `delete_orphan_professors.py` only change data with `--apply`. The unlink id files pin each professor to the RMP id the audit saw, so a link that changed since the audit is skipped.
- **Avoid 08:30 UTC** (the nightly sync) and Saturday 09:00 UTC (the RMP refresh) when running data scripts.
- **Running the backend tests locally.** They need a throwaway Postgres; never point them at Neon (see open item 2):

  ```sh
  docker run -d --rm --name gco-ci-pg -e POSTGRES_USER=gco -e POSTGRES_PASSWORD=gco \
    -e POSTGRES_DB=gco_test -p 5445:5432 postgres:16
  DATABASE_URL=postgresql://gco:gco@localhost:5445/gco_test pytest -q
  ```

## Reference

- [Reconcile the production schema](../runbooks/reconcile-production-schema.md)
- [Delete orphan professors](../runbooks/delete-orphan-professors.md)
- [RMP link audit](../audits/2026-09-29-rmp-link-audit.md), with the id lists `2026-09-29-rmp-links-clearly-wrong.txt` and `2026-09-29-rmp-links-probably-wrong.txt`
- [Critical audit, 2026-09-19](../audits/2026-09-19-critical-audit.md)

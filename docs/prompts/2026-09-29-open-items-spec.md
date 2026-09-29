# Spec: Work through the open items from the 2026-09-29 operations handoff

You are picking up operations work on the **Gaucho Course Optimizer (CoursePick)**, a site where
UCSB students search a course and see its professors ranked by a "Gaucho Score". The score
combines Daily Nexus grade distributions with RateMyProfessors (RMP) ratings.

- **API:** FastAPI on Render (`https://gaucho-course-optimizer.onrender.com`).
- **Frontend:** React on Vercel (coursepick.app).
- **Database:** Postgres 17 on Neon.
- **Scheduled jobs:** GitHub Actions.

**Read `docs/handoff/2026-09-29-operations-handoff.md` first.** It is the source of truth for
where production stands, and it lists the open items this spec turns into tasks. It also covers
the scheduled jobs, what PRs #4 to #14 changed, the hand-run production changes, and the
backups. Read the runbooks in `docs/runbooks/` and the audit in
`docs/audits/2026-09-29-rmp-link-audit.md` when a task needs them. Where a doc and the live
system disagree, trust the live system: check it and report the difference.

---

## 0. Orient before changing anything (read-only)

1. Run `date -u`. Several tasks can't be done until a scheduled run has happened, or until a
   certain date.
2. Run `git fetch` and `git log --oneline -10 origin/master`, then `gh pr list` and
   `gh issue list`. Open issues labelled `uptime` mean production was down.
3. For each scheduled workflow, list its runs since 2026-09-29 and their results with
   `gh run list --workflow <file> --limit 10`. The workflow files are `schedule-sync.yml`,
   `weekly-rmp-refresh.yml`, `weekly-pgdump.yml`, `quarterly-grades.yml` and `uptime.yml`.
4. Take a read-only snapshot of production and compare it with the handoff's table:
   - the Alembic version;
   - the row counts for each table;
   - how many Nexus professors are linked to RMP.

   Explain any big change before you do anything else.
5. Give the user a short status table: each task below, whether it's ready, blocked or done,
   and why. Then proceed.

## 1. Ground rules

### Production safety

- **Production** is Neon project `ancient-river-48578866`, branch `production`
  (`br-steep-hill-akgx2zmo`), database `neondb`. You can run read-only SQL at any time.
- **Ask the user first**, and wait for an explicit yes, before any of these:
  - writing production data. That includes any `--apply`, dispatching the
    "Enhanced professor matching" workflow, and any SQL that writes;
  - deleting a Neon branch;
  - merging a PR;
  - changing Render settings or anything that affects billing;
  - removing git worktrees.

  An approval covers only what it names.
- **Every production data write** follows the same sequence:
  1. rehearse on a new Neon branch copied from `production`;
  2. dry run against production;
  3. create a backup branch named `pre-<task>-YYYY-MM-DD` (instant, no compute needed);
  4. apply;
  5. verify with before and after counts.
- **Don't write data during these windows (UTC):**
  - 08:30 daily (nightly sync);
  - Saturday 09:00 to about 14:00 (RMP refresh);
  - Sunday 06:00 (backup);
  - 10:00 on 25 Jan, Apr, Jul and Oct (grades load).
- **Connection strings:**
  - Get them from the Neon MCP (`get_connection_string`).
  - Use the direct host: drop `-pooler` from the hostname.
  - Pass them only as environment variables. If a command needs a file, put it under
    `.context/` (gitignored) and delete it when you're done.
  - Never commit one, and never echo a password.
- **Never run pytest against Neon.** Until task B1 lands, `tests/conftest.py` reads
  `DATABASE_URL` from `.env` and runs `Base.metadata.drop_all()` at the end of the session.
  Use a throwaway container:

  ```sh
  docker run -d --rm --name gco-ci-pg -e POSTGRES_USER=gco -e POSTGRES_PASSWORD=gco \
    -e POSTGRES_DB=gco_test -p 5445:5432 postgres:16
  DATABASE_URL=postgresql://gco:gco@localhost:5445/gco_test pytest -q
  ```

  On the owner's machine, port 5432 belongs to another project's database.
- **The RMP API needs `RMP_AUTH_TOKEN`.** It's a GitHub secret and is read in
  `scrapers/rmp_scraper.py`. Ask the user for it if it isn't in your environment.

### Git and code conventions

- **Branches:** one branch and one PR per task, each branched from `origin/master`.
- **Stash:** never use a bare `git stash`. If you must stash, push with a unique message and
  `apply` by SHA.
- **Commit messages:** one plain-English sentence ending with a period, then a body that
  explains why.
- **PR bodies:** say what changed, why, and how you verified it.
- **Code:** match the surrounding style and comment density. Every code change needs tests.
  The full backend suite and the frontend checks (lint, `tsc -b`, Vitest) must pass locally
  and in CI.
- **Migrations:** Render does not run them on deploy. If a PR adds one, apply it by hand after
  merging, using `docs/runbooks/reconcile-production-schema.md`.

## 2. Tasks

The groups are:
- **A:** read-only checks.
- **B:** code changes, each ending in a PR.
- **C:** data reviews. The investigation is read-only; writing production data needs approval.
- **D:** housekeeping that depends on dates or approvals.

### A. Check the scheduled runs after the cleanup (read-only)

Do each one once its run has happened. Report what you find. If something needs a production
fix, propose it and wait for approval.

- **A1. Nightly Schedule Sync.** The first run with #10 was 2026-09-30 at 08:30 UTC.
  - The run succeeded.
  - The log shows the unpublished next quarter being skipped, not about 95 UCSB API 400s.
  - The auto-created count is a handful per run. Compare the professor count with the
    handoff's 8,620: a jump of hundreds means orphan rows are being created again.
- **A2. Weekly RMP Refresh.** The first run was Saturday 2026-10-03 at 09:00 UTC, and it takes
  a few hours.
  - The run succeeded.
  - The "already linked" refusals went down from 13.
  - The freed profiles went to their likely owners:

    ```sql
    SELECT id, name_nexus, department, rmp_id, name_rmp, match_confidence
    FROM professors
    WHERE id IN (5630, 6246, 7277, 10165, 10828)
       OR name_nexus IN ('THOMAS C T', 'ALEXANDER A S');
    ```

    Expected:

    | professor | should have RMP profile |
    |---|---|
    | 5630 | 1406150 |
    | 6246 | 845193 |
    | 7277 | 1860302 |
    | 10165 | 2940701 |
    | 10828 | 3049038 |

    THOMAS C T and ALEXANDER A S must **not** be linked to "Thomas Pettus" or
    "Alexander Swan". The given-name guard lets those two through. If they relinked, propose
    unlinking them with pinned ids (`ID:RMP_ID`) through `scripts/unlink_rmp.py`.
  - Check the new links at confidence 85 or above with the method in C1.
- **A3. Weekly Neon DB Backup, Sunday 2026-10-04 06:00 UTC.** The run succeeded and the
  `neon-backup-<run id>` artifact exists.
- **A4. Uptime.** No `uptime` issue is open. If one is, or one was opened and closed, say when
  and why.

### B. Code changes (each is its own PR; they're independent and can run in parallel worktrees)

- **B1. Make the test suite refuse to run against a remote database. Do this first:** it's the
  only open item that could destroy production.
  - Before any engine is created, `tests/conftest.py` should fail with a clear message naming
    the host (never the password) unless `DATABASE_URL` points at `localhost`, `127.0.0.1` or
    `::1`.
  - Allow an explicit override, for example `ALLOW_REMOTE_TEST_DB=1`.
  - Decide whether tests should still load `.env` at all, and justify the choice in the PR.
  - Put the host check in a small function and unit-test it.
  - CI's Postgres service is on `localhost`, so CI must still pass.
  - Update the README's "Running Tests" section.
- **B2. Stop grade loads from creating abbreviated-name duplicate professors.** This must be
  merged before the 2026-10-25 load.
  - **What happened:** on 2026-09-28, 33 professors (ids 101039 to 101075) were created under
    shorter names than their existing rows: `FAVERTY P` versus `FAVERTY P W`, `TAGUE C` versus
    `TAGUE C L`, `DING Y` versus `DING YUFEI`. 132 of their grade rows were exact copies of the
    existing rows' grades. Pass 4 merged them on 2026-09-29. The full list is in the log of
    Actions run 36611045061.
  - **Investigate first:**
    - Fetch the current Daily Nexus CSV (`scrapers/grades_ingester.py`, `fetch_grades_csv`).
    - Find out how these instructors' names appear across years.
    - Explain why the loader re-inserted their history. `scrapers/grades_loader.py` matches
      `name_nexus` exactly.
  - **Then prevent it:**
    - When an incoming name has no exact match, resolve it to an existing professor in the same
      department only when exactly one candidate fits. Use the same rule pass 4 uses
      (`etl/name_utils.find_duplicate_pairs`). Otherwise create the professor as today.
    - Don't duplicate grade rows the resolved professor already has.
    - Add tests that reproduce the `FAVERTY P` / `FAVERTY P W` case and an ambiguous case,
      for example two `WOODS M *` rows.
  - **Prove it on a Neon branch copied from production:**
    1. run the loader with the current CSV;
    2. run `run_enhanced_matching(session, dry_run=True)`;
    3. show that pass 4 finds no new pairs from the load.

    Don't touch production.
- **B3. Make migrations reach production. The user decides which option.**
  - **Background:** Render never runs `preDeployCommand`. It's probably a free instance, or a
    service that isn't attached to the Blueprint; see section 6 of the schema runbook.
  - **Options.** Lay these out for the user with a recommendation, and implement only the one
    they choose:
    - **(a) Fix it in Render.** Only the user can check the dashboard, and paid instance types
      cost money. No code.
    - **(b) Add a `migrate.yml` workflow.** It runs on pushes to master that touch
      `db/migrations/**`, and on manual dispatch. It runs `alembic upgrade head` with the
      `DATABASE_URL` secret, then checks that `alembic current` is head and that
      `compare_metadata` is empty. It needs a concurrency group. The Render deploy and the
      migration race each other, so migrations must work with both the old and the new code.
      Check whether the secret uses the pooler host: migrations are safer on the direct host.
    - **(c) Detect drift.** A scheduled check fails, or opens one issue, when production's
      `alembic_version` is behind the repo's head. It's cheap and catches drift whatever
      happens with (a) or (b).

### C. Data reviews (investigation is read-only; production writes need approval)

- **C1. Review the 24 hidden probably-wrong RMP links.**
  - **Which links:** the lines in `docs/audits/2026-09-29-rmp-links-probably-wrong.txt` except
    5540, 5787, 6618, 9905, 10360, 10865 and 11029, which are already handled.
  - **Look up each RMP profile.** POST to `https://www.ratemyprofessors.com/graphql` with
    `Authorization: Basic $RMP_AUTH_TOKEN`, using `curl_cffi` with `impersonate="chrome"` like
    the scraper does. Query `node(id: base64("Teacher-<rmp_id>"))` for `firstName`,
    `lastName`, `department`, `numRatings`, and the class codes of a few ratings.
  - **Compare** that with the professor's Nexus department and the courses in their grade rows
    (SQL).
  - **Classify** each link as wrong, right or unsure, with the evidence in a table.
  - **After approval**, unlink the wrong ones with pinned `ID:RMP_ID` lines through
    `scripts/unlink_rmp.py`, following the production write sequence in section 1. Record the
    decisions in the status note at the top of the audit.
  - Do this after A2 if you can, because the refresh can change links. The pinned ids make the
    script skip any link that changed.
- **C2. The 4 pairs pass 4 skipped:**
  - `RAVEN M` (101052) has grades that conflict with `RAVEN M A` (7491, MCDB).
  - 101060 matches two `KOTH M K` rows.
  - 101066 matches `WOODS M J` and `WOODS M P`.
  - 101067 matches two `BUENO CACHADI` rows.

  For each, compare the courses, years and grade rows, and recommend a resolution. Where there
  are two rows with the same full name, those rows may themselves be duplicates. Don't merge
  without approval. If a merge is approved, rehearse it on a Neon branch with
  `etl/enhanced_matcher._merge_pair` inside one transaction, then run it on production.

### D. Housekeeping

- **D1. Backup branches.** After 2026-10-06, if A1 to A3 look healthy, ask the user whether to
  delete `pre-schema-reconcile-2026-09-29` (`br-late-dew-akbqg144`) and
  `pre-data-cleanup-2026-09-29` (`br-restless-cloud-ak2ucy84`). List any branches you create,
  each with a suggested deletion date.
- **D2. Old agent worktrees**, if any exist. On the owner's machine, `git worktree list` showed
  5 leftover agent worktrees under `.claude/worktrees/`, all on merged branches. Ask before
  removing them, and only remove ones with no uncommitted changes.
- **D3. After the 2026-10-25 grades load:**
  - If B2 has landed, run pass 4 as a dry run on a Neon branch to confirm there are no new
    duplicates.
  - If B2 hasn't landed, rehearse pass 4 on a branch, review every merge, and ask before
    dispatching the "Enhanced professor matching" workflow.

## 3. Suggested order

1. Orient (section 0) and report.
2. B1.
3. B2 and B3, in parallel worktrees, one PR each. Background agents are fine for these. B2
   must merge before 2026-10-25.
4. The A tasks, as their runs happen.
5. C1 and C2, ideally after A2.
6. The D tasks.

Keep the data tasks (C, D1, D3) in the main session, because they need the user's approval at
each step.

## 4. Done when

- Every task has one of: a merged PR; an approved and verified production change with its
  before and after counts; or a written decision to defer it, with the reason.
- There's a new `docs/handoff/<date>-operations-handoff.md` with the updated state and open
  items, and `.planning/STATE.md` points at it.
- The user has a final report with:
  - a table of the tasks and their status;
  - the PR links;
  - each production change with its counts;
  - the backup branches and when to delete them.

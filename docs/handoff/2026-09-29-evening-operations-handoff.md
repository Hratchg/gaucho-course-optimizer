# Operations handoff, 2026-09-29 (evening)

Start here. This session worked through
[the open-items spec](../prompts/2026-09-29-open-items-spec.md), which was built from
[the morning handoff](2026-09-29-operations-handoff.md). That handoff still holds the details
of the earlier work: the scheduled-jobs table, the runbooks, and the 2026-09-28/29 production
changes.

It turned up four new problems, recorded below as B4, B5, C3 and the uptime cadence. Three
PRs wait on the owner's decision.

Everything below was checked at about 23:30 UTC on 2026-09-29.

## Where things stand

- **master** is at `c67474c`, and CI is green.
- **API:** `/ready` returns 200.
- **Database:** Neon project `ancient-river-48578866`, branch `production` (`br-steep-hill-akgx2zmo`).
  - The schema is at Alembic head `9acf49a4b131`.
  - `scripts/check_migration_drift.py` (PR #20) reports it in sync: the models match the schema.

Production row counts:

| | count | change since the morning handoff |
|---|---:|---|
| professors | 8,616 (6,797 distinct Nexus names) | −4: C2 merges |
| Nexus professors linked to RMP | 926 (153 at confidence 85 or above) | |
| RMP-only rows | 343 | |
| grade_distributions | 105,729 (latest year 2026) | −3: duplicate rows dropped by the C2 merges |
| scheduled_sections | 12,439 (20262, 20263, 20264) | |
| rmp_ratings / rmp_comments | 1,581 / 13,858 | |
| gaucho_scores | 10,962 | |

## Open PRs waiting for a merge decision

| PR | What | What merging does |
|---|---|---|
| [#19](https://github.com/Hratchg/gaucho-course-optimizer/pull/19) | **B4.** The schedule sync matches the instructor's full UCSB name and the section's department. Before this, it took the first professor with a similar surname. | **Changes production data at the next nightly.** In Fall 2026, about 340 sections move to another professor, and about 290 sections get a newly auto-created professor (112 new rows). |
| [#20](https://github.com/Hratchg/gaucho-course-optimizer/pull/20) | **B3, option (c).** A daily read-only migration drift check that opens one `migration-drift` issue. | Adds a workflow. It only reads production. |
| [#21](https://github.com/Hratchg/gaucho-course-optimizer/pull/21) | **C3.** A plan to fold the 1,476 same-name duplicate professor rows into their keepers. | Docs only. Running the plan is a separate approval. |

CI is green on all three.

## Open items, in order

1. **Nightly Schedule Sync, 2026-09-30** (A1).
   - **When:** scheduled for 08:30 UTC, but runs have started between 13:00 and 17:00.
   - **Next quarter:** check that 20271 is skipped with one INFO line (#10), with no UCSB 400s.
   - **`auto_created`:** what to expect depends on #19.
     - If #19 **isn't** merged: expect a handful. Hundreds would mean the orphan-professor bug is back.
     - If #19 **is** merged before the run: expect about **112**. That's the intended one-time cost of no longer guessing.

       Then check two things. The run after it should auto-create only a handful again. And `POPESCU P F` should now have its roughly 129 PHYS sections.
2. **Weekly RMP Refresh, Saturday 2026-10-03** (A2). Check what the morning handoff lists:
   - the five freed profiles went to their likely owners;
   - fewer "already linked" refusals than the 13 seen on 2026-09-28;
   - THOMAS C T and ALEXANDER A S weren't relinked to "Thomas Pettus" or "Alexander Swan". Unlink them again if they were.
3. **Weekly Neon DB Backup, Sunday 2026-10-04 06:00 UTC** (A3). The run should be green and the artifact present.
4. **Review the 24 probably-wrong RMP links** (C1).
   - **Blocked:** it needs `RMP_AUTH_TOKEN`. Put `RMP_AUTH_TOKEN=...` in `.context/rmp.env`, which is gitignored; never commit it.
   - **Timing:** do it after the Saturday refresh, which can change links.
   - **Method:** in spec section C1.
5. **Decide on #19, and then on past quarters.** The nightly only re-sets the current and next quarter. Fixing 20262 and 20263 needs a one-off re-point with the new matcher, which is a production write.
   - **Estimate** (stored professor vs new matcher, 2026-09-29 snapshot):

     | Quarter | To another professor | No match (auto-create) | Duplicate row → keeper (C3) |
     |---|---|---|---|
     | 20262 | 468 | 271 (127 names) | 2,586 |
     | 20263 | 108 | 79 (44 names) | 735 |

   - **Overlap with C3:** the re-point would also move all of C3's sections.
   - **Procedure:** rehearse on a branch, dry-run, take a backup branch, apply, verify.
6. **C3: run the plan in #21** once it's approved.
   - It re-points 3,323 sections to their keeper rows.
   - Then `scripts/delete_orphan_professors.py` deletes the 1,476 rows (8,616 → 7,140 professors).
   - Every one of those sections carries exactly the keeper's name, so the result is the same with or without #19.
7. **C2 leftovers:**
   - **WOODS:** once C3 has run, merge `WOODS M` (101066) into `WOODS M J` (10233). Details below.
   - **RAVEN M** (101052) stays unmerged.
8. **B5: the schedule sync never fetches departments whose UCSB code contains a space.** New and not fixed. Details below.
9. **Delete the backup branches after about 2026-10-06** (D1), if items 1 to 3 look healthy. See "Backups" below.
10. **After the Quarterly Grades Update on 2026-10-25** (D3).
    - #18 has landed, so the load should create no abbreviated-name duplicates.
    - Confirm it:
      - on a Neon branch copied from production after the load, run pass 4 as a dry run;
      - expect no new pairs;
      - the loader's log should show "abbreviated names resolved" and no burst of "professors created".

## What this session did

| Task | Status |
|---|---|
| A1: nightly sync check | Deferred to 2026-09-30 (item 1). |
| A2: RMP refresh check | Deferred to 2026-10-03 (item 2). |
| A3: backup check | Deferred to 2026-10-04 (item 3). |
| A4: uptime | Done. No open `uptime` issue. `/ready` returned 500 from 2026-09-24 22:37 to 2026-09-28 19:40 UTC; that was before #8 and has since recovered. New finding: see "Uptime cadence" below. |
| B1: the test suite refuses a remote DB | Merged, [#17](https://github.com/Hratchg/gaucho-course-optimizer/pull/17). |
| B2: grade loader resolves abbreviated names | Merged, [#18](https://github.com/Hratchg/gaucho-course-optimizer/pull/18). Rehearsed on a production copy with the 2026 CSV: 0 rows inserted, 0 professors created, 33 names resolved. The old loader on the same data inserted 136 rows and created 33 duplicates. |
| B3: migrations reach production | The owner chose option (c): [#20](https://github.com/Hratchg/gaucho-course-optimizer/pull/20), open. Options (a) and (b) weren't taken, so migrations are still applied by hand; #20 reminds you. |
| B4 (new): sync misattribution | [#19](https://github.com/Hratchg/gaucho-course-optimizer/pull/19), open. |
| B5 (new): multi-word departments never synced | Recorded here, not fixed. |
| C1: 24 probably-wrong links | Blocked on `RMP_AUTH_TOKEN` (item 4). |
| C2: 4 pairs pass 4 skipped | KOTH and BUENO merged in production. WOODS waits on C3; RAVEN deferred. |
| C3 (new): same-name duplicates | Plan, [#21](https://github.com/Hratchg/gaucho-course-optimizer/pull/21), open. |
| D1: backup branches | After 2026-10-06 (item 9). |
| D2: old agent worktrees | Done. The owner approved removing the 5 leftover worktrees; all were clean and on merged branches (#10 to #14). |
| D3: after the 2026-10-25 load | Item 10. |

## Production changes made (2026-09-29 evening)

**C2 merges, about 21:03 UTC.**

- **What merged:** each duplicate went into the oldest full-name row, using `etl.enhanced_matcher._merge_pair` in one transaction.
  - `KOTH M K`: 95297 and 101060 → 9686.
  - `BUENO CACHADI`: 81352 and 101067 → 5355.
- **Before merging:**
  - rehearsed on the Neon branch `c2-merge-rehearsal-2026-09-29`;
  - dry-ran against production with an expected-delta assertion;
  - took the backup branch `pre-c2-merges-2026-09-29`.

| | before | after |
|---|---:|---:|
| professors | 8,620 | 8,616 |
| grade_distributions | 105,732 | 105,729 (3 exact duplicate rows dropped) |
| scheduled_sections | 12,439 | 12,439 (3 re-pointed) |
| rmp_ratings / gaucho_scores | unchanged | unchanged |

The rehearsal also loaded the 2026 CSV after the merges: 0 rows inserted and 0 professors created. So the next grade load won't recreate them.

**Not merged, with reasons:**

- **RAVEN M (101052).** Its MCDB 126BL Winter 2015 row has different numbers from `RAVEN M A`'s (7491), so it's another section or another instructor.
  - **If summed:** the student counts would be wrong.
  - **If dropped:** a student record would be lost.
  - **Either way:** `RAVEN M A` would have two rows for one key, and #18's conflict rule would recreate `RAVEN M` at the next load.
  - **Decision:** leave it.
- **WOODS M (101066).**
  - **Who it is:** its only grade row (EDIA321, 2020) is the same course as `WOODS M J` (10233, ED).
  - **The blocker:** `WOODS M P` row 95409 is also in ED. While it exists, the grade loader sees two full names for `WOODS M` and would recreate 101066 after a merge.
  - **The fix:** C3 folds 95409 into its keeper 15235 (MUS). Then merge 101066 into 10233 and prove on a branch that a CSV load inserts nothing. That merge needs its own approval.

## New problems found

- **B4: the nightly sync attached sections to the wrong professor.**
  - **Scale:** 352 Fall 2026 sections from 119 instructors.
  - **Examples:**
    - `POPESCU P F` → `POPESCU P E`;
    - `ZHAO XIAOLEI` (MATH) → `ZHAO B Y` (CMPSC);
    - three different PSTAT `WANG Y…` → `WANG Y-D`;
    - `KIM TAEHWAN` (MATH) → `KIM T` (MAT).
  - **Cause:** the matcher used only the surname and first initial and returned the first row in id order.
  - **Status:** fixed in #19. Past quarters need item 5.
- **B5: departments whose UCSB subject code has a space have never had a schedule section.**
  - **Cause:** `Course.department` keeps only the first word of the code, so the nightly asks UCSB for the wrong code.
  - **Affected, all with grades through 2026:**

    | Department | Stored as | Courses |
    |---|---|---:|
    | RG ST | `RG` | 457 |
    | CH E | `CH` | 246 |
    | POL S | `POL` | 233 |
    | ENV S | `ENV` | 216 |
    | C LIT | `C` | 135 |
    | BL ST | `BL` | 119 |
    | AS AM | `AS` | 102 |

    That's 1,508 courses with 0 scheduled sections.
  - **Two more with 0 sections, probably for a different reason:** `ES` (69 courses) and `W&L` (50) are single-word codes. The `&` may need URL-encoding, and ES may not be what UCSB calls those courses. Check them while fixing B5.
  - **Where to start:** `scrapers/grades_ingester` (how the department is parsed) and `db.queries.get_departments`.
  - **Watch for:** professors store the same truncated codes (`POL`, `CH`, `RG`). A fix must keep the section's department comparable with the professor's department, which #19's matcher compares.
  - **Knock-on:** once fixed, these departments' instructors go through the matcher for the first time, so expect a one-time burst of auto-created professors.
- **C3: 1,476 same-name duplicate professor rows remain from the old sync.**
  - Only past-quarter sections reference them.
  - Plan in #21.
- **Uptime cadence.**
  - `uptime.yml` is scheduled every 15 minutes, but GitHub has been running it only every 4 to 6 hours. So an outage can go unnoticed for hours.
  - If faster detection matters, use an external pinger. That's an owner decision: it's a new service and may cost money.
- **Unreferenced auto-created rows.**
  - After #19 (and the past-quarter re-point), some rows the old matcher created can lose all their sections.
  - The orphan script keeps the oldest row of every name, so rows with a unique name stay.
  - This is harmless, but worth a later decision.

## Backups and Neon branches

| Branch | ID | What it is | Delete |
|---|---|---|---|
| `pre-schema-reconcile-2026-09-29` | `br-late-dew-akbqg144` | Production before the migration | after about 2026-10-06 |
| `pre-data-cleanup-2026-09-29` | `br-restless-cloud-ak2ucy84` | Production before the unlink, the orphan delete and pass 4 | after about 2026-10-06 |
| `pre-c2-merges-2026-09-29` | `br-lucky-tree-aktx5ki1` | Production just before the C2 merges | after about 2026-10-06 |
| `b2-loader-rehearsal-2026-09-29` | `br-bitter-hat-akgdmt6j` | #18 rehearsal (new loader) | any time: no longer needed |
| `b2-old-loader-contrast-2026-09-29` | `br-orange-term-ak0xm5bf` | #18 rehearsal (old loader) | any time: no longer needed |
| `c2-merge-rehearsal-2026-09-29` | `br-damp-firefly-ak0ubjpz` | C2 rehearsal | any time: no longer needed |

- **Other backups:** the pg_dump artifact `neon-backup-36607600841` is kept until about 2026-12-28.
- **Approval:** deleting any branch needs the owner's approval.

## Scheduled jobs

These are unchanged from the morning handoff, plus one:

| Workflow file | When (UTC) | What it does | Secrets |
|---|---|---|---|
| `migration-drift.yml` (#20, once merged) | daily 20:00, on pushes to master that touch `db/migrations/**` or `db/models.py`, and by hand | Read-only. It compares production's `alembic_version` and schema with master, and opens or refreshes one `migration-drift` issue, which closes itself once production is in sync. | `DATABASE_URL` |

## Working safely

Same as [the morning handoff](2026-09-29-operations-handoff.md#working-safely), plus:

- **The test suite now refuses a remote database** (#17). It uses `localhost:5432/gco_test` unless `DATABASE_URL` is set. Set `ALLOW_REMOTE_TEST_DB=1` only for a scratch database you mean to wipe.
- **Every production data write follows the same sequence:**
  1. rehearse on a Neon branch copied from production;
  2. dry-run against production;
  3. create a backup branch `pre-<task>-YYYY-MM-DD` with no compute;
  4. apply;
  5. verify with before and after counts.
- **Check the knock-on effects of each fix on the other pipelines:**
  - the nightly sync;
  - the grade loader's abbreviated-name resolver;
  - pass 4;
  - the RMP refresh.

  Several of this session's findings came from exactly that. For example, a WOODS merge would have been undone by the next grade load.

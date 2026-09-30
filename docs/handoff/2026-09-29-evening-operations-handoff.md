# Operations handoff, 2026-09-29 (evening)

Start here. This session worked through
[the open-items spec](../prompts/2026-09-29-open-items-spec.md), which was built from
[the morning handoff](2026-09-29-operations-handoff.md). That handoff still holds the details
of the earlier work: the scheduled-jobs table, the runbooks, and the 2026-09-28/29 production
changes.

It turned up four new problems, recorded below as B4, B5, C3 and the uptime cadence.

Early on 2026-09-30 (UTC) the owner approved everything that was waiting:

- #19, #20 and #21 were merged.
- The C3 plan, the past-quarter re-point and the WOODS merge ran on production. See "Production changes made (2026-09-30)".
- The checks after those writes found one more problem, **B6**. It was fixed the same day by [#23](https://github.com/Hratchg/gaucho-course-optimizer/pull/23).
- The 2026-09-30 nightly, #19's first run, was checked (item 1).

Everything below was checked at about 05:50 UTC on 2026-09-30.

## Where things stand

- **master** has #19 and #20 (`bb1a65b`), plus #21 and this handoff (#22) once merged. CI is green.
- **API:** `/ready` returns 200.
- **Database:** Neon project `ancient-river-48578866`, branch `production` (`br-steep-hill-akgx2zmo`).
  - The schema is at Alembic head `9acf49a4b131`.
  - The drift check from #20 ran once by hand in CI ([run 36674265022](https://github.com/Hratchg/gaucho-course-optimizer/actions/runs/36674265022)). It reported "In sync", and there is no `migration-drift` issue.

Production row counts:

| | count | change since the morning handoff |
|---|---:|---|
| professors | 7,277 (6,934 distinct Nexus names) | −4: C2 merges (8,616). −1,476: C3. +138: past-quarter re-point. −1: WOODS. |
| Nexus professors linked to RMP | 926 (153 at confidence 85 or above) | |
| RMP-only rows | 343 | |
| grade_distributions | 105,728 (latest year 2026) | −3: C2 merges. −1: WOODS merge (exact duplicate rows dropped). |
| scheduled_sections | 12,439 (20262, 20263, 20264) | 4,249 re-pointed on 2026-09-30 (3,323 by C3, 926 by the past-quarter re-point) |
| rmp_ratings / rmp_comments | 1,581 / 13,858 | |
| gaucho_scores | 10,962 | |

## PRs merged on 2026-09-30

| PR | What | Effect |
|---|---|---|
| [#20](https://github.com/Hratchg/gaucho-course-optimizer/pull/20) | **B3, option (c).** A daily read-only migration drift check that opens one `migration-drift` issue. | The first run, by hand, reported "In sync". |
| [#19](https://github.com/Hratchg/gaucho-course-optimizer/pull/19) | **B4.** The schedule sync matches the instructor's full UCSB name and the section's department. Before this, it took the first professor with a similar surname. | **Changes production data at the next nightly**: about 354 Fall 2026 sections move to another professor, and about 119 sections get a newly created professor (about 49 rows). See item 1. |
| [#21](https://github.com/Hratchg/gaucho-course-optimizer/pull/21) | **C3.** The same-name duplicates plan, with an "Execution" section recording the 2026-09-30 run. | Docs only. |

## Open items, in order

1. **Nightly Schedule Sync, 2026-09-30** (A1). **Done**: [run 36733952342](https://github.com/Hratchg/gaucho-course-optimizer/actions/runs/36733952342), 15:04 UTC, green. It was #19's first run.

   | | forecast | actual |
   |---|---:|---:|
   | Professors created ("Auto-created professor record" lines) | about 49 | 72 |
   | `auto_created` (counts sections) | about 119 | 166 |

   - **The extra professors:** they're mostly instructors newly assigned in UCSB's data since the forecast (ME, PHYS, PSY). No professor name appears twice. Professors: 7,277 → 7,349.
   - **Next quarter:** 20271 was skipped with one INFO line, and there were no errors.
   - **`POPESCU P F`:** has all 129 of his sections (46 in 20262, 33 in 20263, 50 in 20264).
   - **Still to check:** the next nightly (2026-10-01) should auto-create only a handful.
2. **Weekly RMP Refresh, Saturday 2026-10-03** (A2). Check what the morning handoff lists:
   - the five freed profiles went to their likely owners;
   - fewer "already linked" refusals than the 13 seen on 2026-09-28;
   - THOMAS C T and ALEXANDER A S weren't relinked to "Thomas Pettus" or "Alexander Swan". Unlink them again if they were.
3. **Weekly Neon DB Backup, Sunday 2026-10-04 06:00 UTC** (A3). The run should be green and the artifact present.
4. **Review the 24 probably-wrong RMP links** (C1).
   - **Blocked:** it needs `RMP_AUTH_TOKEN`. Put `RMP_AUTH_TOKEN=...` in `.context/rmp.env`, which is gitignored; never commit it.
   - **Reminder:** the owner has one. It was emailed to them on 2026-09-30: "Reminder (on or after Sat Oct 3, 2026): give Claude the RMP token for the CoursePick C1 review".
   - **Timing:** do it after the Saturday refresh, which can change links.
   - **Method:** in spec section C1.
5. **B6: fixed by [#23](https://github.com/Hratchg/gaucho-course-optimizer/pull/23), merged 2026-09-30.** Short-name professors created by the sync would have got copies of grades that are already stored. Details under "New problems found". Confirm at the 2026-10-25 load (item 10).
6. **Review one pair pass 4 would now merge:** `YIN Y` (101113) into `YIN YOUWEI` (101117), CHEM.
   - Found by a pass 4 dry run after the C3 cleanup. Not merged.
   - Dispatching "Enhanced professor matching" would merge it. That's a production write, so check the pair first.
7. **RAVEN M** (101052) stays unmerged (C2).
8. **B5: the schedule sync never fetches departments whose UCSB code contains a space.** New and not fixed. Details below.
9. **Delete the Neon branches** (D1), if items 1 to 3 look healthy. See "Backups" below.
   - **From about 2026-10-06:** the 2026-09-29 backups.
   - **From about 2026-10-07:** the 2026-09-30 backups.
   - **Any time:** the rehearsal branch.
10. **After the Quarterly Grades Update on 2026-10-25** (D3).
    - #18 and #23 have landed, so the load should create no abbreviated-name duplicates and copy no grades onto sync-created short names (`SCHMITT R`, `ZHANG W`, `MARTIN J`).
    - Confirm it:
      - on a Neon branch copied from production after the load, run pass 4 as a dry run;
      - expect no new pairs;
      - the loader's log should show "abbreviated names resolved" and no burst of "professors created".

## What this session did

| Task | Status |
|---|---|
| A1: nightly sync check | Done on 2026-09-30 (item 1). |
| A2: RMP refresh check | Deferred to 2026-10-03 (item 2). |
| A3: backup check | Deferred to 2026-10-04 (item 3). |
| A4: uptime | Done. No open `uptime` issue. `/ready` returned 500 from 2026-09-24 22:37 to 2026-09-28 19:40 UTC; that was before #8 and has since recovered. New finding: see "Uptime cadence" below. |
| B1: the test suite refuses a remote DB | Merged, [#17](https://github.com/Hratchg/gaucho-course-optimizer/pull/17). |
| B2: grade loader resolves abbreviated names | Merged, [#18](https://github.com/Hratchg/gaucho-course-optimizer/pull/18). Rehearsed on a production copy with the 2026 CSV: 0 rows inserted, 0 professors created, 33 names resolved. The old loader on the same data inserted 136 rows and created 33 duplicates. |
| B3: migrations reach production | The owner chose option (c): [#20](https://github.com/Hratchg/gaucho-course-optimizer/pull/20), merged 2026-09-30 and run once by hand ("In sync"). Options (a) and (b) weren't taken, so migrations are still applied by hand; #20 reminds you. |
| B4 (new): sync misattribution | [#19](https://github.com/Hratchg/gaucho-course-optimizer/pull/19), merged 2026-09-30. Past quarters re-pointed on production the same day. |
| B5 (new): multi-word departments never synced | Recorded here, not fixed. |
| C1: 24 probably-wrong links | Blocked on `RMP_AUTH_TOKEN` (item 4). |
| C2: 4 pairs pass 4 skipped | KOTH and BUENO merged on 2026-09-29. WOODS merged on 2026-09-30, after C3. RAVEN deferred. |
| C3 (new): same-name duplicates | Plan [#21](https://github.com/Hratchg/gaucho-course-optimizer/pull/21), merged. Run on production on 2026-09-30. |
| B6 (new): short-name auto-creates get copied grades | Found by the 2026-09-30 checks. Fixed by [#23](https://github.com/Hratchg/gaucho-course-optimizer/pull/23), merged the same day. |
| D1: backup branches | After 2026-10-06 (item 9). |
| D2: old agent worktrees | Done. The owner approved removing the 5 leftover worktrees; all were clean and on merged branches (#10 to #14). This session's own worktrees were removed after its PRs merged. |
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
  - **The fix:** C3 folds 95409 into its keeper 15235 (MUS). Then merge 101066 into 10233 and prove on a branch that a CSV load inserts nothing. Done on 2026-09-30, with approval: the rehearsal load inserted no `WOODS M` row.

## Production changes made (2026-09-30, 05:47–05:50 UTC)

The owner approved all three, and they ran from master `bb1a65b` after a rehearsal on `prod-writes-rehearsal-2026-09-30`. The rehearsal gave the same counts. The plan in #21 has the full record ("Execution").

| Step | Backup branch taken first | Result |
|---|---|---|
| **C3:** re-point the sections on same-name duplicates to the keeper, then `scripts/delete_orphan_professors.py --apply` | `pre-same-name-dedup-2026-09-30` | 3,323 sections re-pointed. 1,476 rows deleted. Professors 8,616 → 7,140. Same-name duplicates: 0. |
| **Past-quarter re-point:** 20262/20263 through #19's matcher, mirroring `sync_department_sections` | `pre-past-quarter-repoint-2026-09-30` | 926 sections changed: 576 to another existing professor, 350 to 138 newly created professors. Professors 7,140 → 7,278. |
| **WOODS:** `_merge_pair(101066 → 10233)` | `pre-woods-merge-2026-09-30` | Professors 7,278 → 7,277. Grades 105,729 → 105,728: one exact duplicate row dropped. |

Sections, ratings, comments, scores and `alembic_version` didn't change.

**Checks afterwards:**

- No section points at a missing professor.
- A second re-point run changes nothing.
- **Tonight's matcher, replayed over 20264/20271 before and after:** it differs only on 175 sections, which now reuse a row the re-point created under the same name.
- **Moves reviewed:** 557 of the 576 moves go to a row whose name is exactly the UCSB name (for example `AFIFI W A` had been on `AFIFI T D`).
- **API:** `/ready` and the course endpoints return 200, and no professor is listed twice.
- **Grades CSV load on the rehearsal branch:** 0 professors created and no `WOODS M` row, so WOODS is settled. But it inserted 6 rows, which is B6.

**Undo:** restore the backup branch taken before the step. The operator's local `.context/` also has the section mappings (`c3-mapping-production.csv`, `repoint-mapping-production.csv`), but they aren't committed.

## New problems found

- **B4: the nightly sync attached sections to the wrong professor.**
  - **Scale:** 352 Fall 2026 sections from 119 instructors.
  - **Examples:**
    - `POPESCU P F` → `POPESCU P E`;
    - `ZHAO XIAOLEI` (MATH) → `ZHAO B Y` (CMPSC);
    - three different PSTAT `WANG Y…` → `WANG Y-D`;
    - `KIM TAEHWAN` (MATH) → `KIM T` (MAT).
  - **Cause:** the matcher used only the surname and first initial and returned the first row in id order.
  - **Status:** fixed in #19, merged 2026-09-30. Past quarters were re-pointed on production the same day.
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
- **C3: 1,476 same-name duplicate professor rows remained from the old sync.**
  - Only past-quarter sections referenced them.
  - Removed on 2026-09-30; see above.
- **B6: sync-created short names would have received copies of existing grades at the next grade load.** Fixed by #23; see the end of this entry.
  - **What happens:** #19 matches only within the section's department. When a UCSB name like `SCHMITT R` has a full-name row only in another department, the sync creates a short-name row. Here the ESM/GEOG sections are taught by `SCHMITT R J` (5995), stored as `ENV`, the truncated `ENV S` from B5. The grade loader then matches the CSV's `SCHMITT R` exactly to that new row, instead of resolving it to `SCHMITT R J` as #18 does. So it stores those grades a second time.
  - **Measured on the rehearsal branch** (the 2026-09-30 writes, then a simulated nightly, then the current CSV): 12 copied rows.

    | Row | Copied rows | Copied from |
    |---|---:|---|
    | `SCHMITT R` (ESM) | 6 | `SCHMITT R J` (ENV) |
    | `ZHANG W` (ECON) | 4 | `ZHANG WEIDI` (ART) |
    | `MARTIN J` (EARTH) | 2 | `MARTIN J A` (HIST) |

    `SCHMITT R` was created by the past-quarter re-point, and the other two by the 2026-09-30 nightly.
  - **Cause:** #19 together with #18. The nightly alone creates all three names.
  - **Deadline:** the next grade load, 2026-10-25. Met: nothing had been copied yet.
  - **Fix ([#23](https://github.com/Hratchg/gaucho-course-optimizer/pull/23)):** a name whose rows hold no grades and no RMP identity now goes through #18's abbreviated-name rule, as if the row didn't exist. When that rule doesn't apply, the grades go to the sync's row as before.
    - **Rehearsal:** on a production copy with the nightly simulated, the CSV load inserted 0 rows (master: 12) and created 0 professors.
    - **Left open:** the sections stay on the short-name rows, so `SCHMITT R` still shows on its ESM courses without grades. Merging these rows into the full names is a separate decision. Watch B5: its truncated departments are part of the cause.
- **Uptime cadence.**
  - `uptime.yml` is scheduled every 15 minutes, but GitHub has been running it only every 4 to 6 hours. So an outage can go unnoticed for hours.
  - If faster detection matters, use an external pinger. That's an owner decision: it's a new service and may cost money.
- **Unreferenced auto-created rows.**
  - After #19, some rows the old matcher created can lose all their sections. The past-quarter re-point left none; the 2026-09-30 nightly may have left a few.
  - Production has 10 rows with no references and no RMP identity (2026-09-30).
  - The orphan script keeps the oldest row of every name, so rows with a unique name stay.
  - This is harmless, but worth a later decision.

## Backups and Neon branches

| Branch | ID | What it is | Delete |
|---|---|---|---|
| `pre-schema-reconcile-2026-09-29` | `br-late-dew-akbqg144` | Production before the migration | after about 2026-10-06 |
| `pre-data-cleanup-2026-09-29` | `br-restless-cloud-ak2ucy84` | Production before the unlink, the orphan delete and pass 4 | after about 2026-10-06 |
| `pre-c2-merges-2026-09-29` | `br-lucky-tree-aktx5ki1` | Production just before the C2 merges | after about 2026-10-06 |
| `pre-same-name-dedup-2026-09-30` | `br-cool-term-akmghnsq` | Production just before C3 | after about 2026-10-07 |
| `pre-past-quarter-repoint-2026-09-30` | `br-lingering-cell-ak2sk3oa` | Production after C3, before the past-quarter re-point | after about 2026-10-07 |
| `pre-woods-merge-2026-09-30` | `br-wild-term-akcrjj4z` | Production after the re-point, before the WOODS merge | after about 2026-10-07 |

- **Already deleted, with the owner's approval on 2026-09-30:**
  - the three 2026-09-29 rehearsal branches;
  - `prod-writes-rehearsal-2026-09-30`;
  - `b6-loader-rehearsal-2026-09-30`, the #23 rehearsal.
- **Branch limit:** that leaves 6 non-production branches plus `production`. The free plan allows about 10.

- **Other backups:** the pg_dump artifact `neon-backup-36607600841` is kept until about 2026-12-28.
- **Approval:** deleting any branch needs the owner's approval.

## Scheduled jobs

These are unchanged from the morning handoff, plus one:

| Workflow file | When (UTC) | What it does | Secrets |
|---|---|---|---|
| `migration-drift.yml` (#20) | daily 20:00, on pushes to master that touch `db/migrations/**` or `db/models.py`, and by hand | Read-only. It compares production's `alembic_version` and schema with master, and opens or refreshes one `migration-drift` issue, which closes itself once production is in sync. | `DATABASE_URL` |

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

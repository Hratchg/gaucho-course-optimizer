# Plan: fold the 1,476 same-name duplicate professor rows into their keepers

**Status:** plan only. Nothing here has run against production. Every production step below needs the owner's explicit approval. Each one follows the write sequence in section 1 of `docs/prompts/2026-09-29-open-items-spec.md`:

1. rehearse on a Neon branch;
2. dry-run against production;
3. create a backup branch;
4. apply;
5. verify the counts.

Numbers are from read-only queries on production, 2026-09-29 around 23:30 UTC. Re-measure them at the dry run.

## What they are

A "same-name duplicate" is a `professors` row whose `name_nexus` is exactly the name of an older row, which is the keeper. The old nightly sync created these rows before PR #1 (commit 4337c14), one per unmatched instructor per night.

- **What PR #13 did:** it deleted the 84,034 duplicate rows that nothing referenced.
- **What's left:** the rows below survived because a past-quarter section still points at them. The nightly only re-sets sections for the current and next quarter.

| | Count |
|---|---|
| Duplicate rows | **1,476**, under 1,199 names |
| Sections pointing at them | **3,323**: 2,586 in 20262, 735 in 20263, 2 in 20264 |
| Grades, RMP ratings, Gaucho scores on them | 0, 0, 0 |
| Rows with an RMP identity (`rmp_id` or `name_rmp`) | 0 |
| Sections whose UCSB name isn't exactly the row's name | 0 |
| Rows whose keeper changes if names are compared case- and space-insensitively | 0 |
| Rows in a different department from their keeper | 164 (152 names, 395 sections) |

So only sections reference these rows, and every such section carries exactly the keeper's name. Both the old matcher and the new one (PR #19) send that name to the keeper, because an exact `name_nexus` match wins and the oldest row wins among equals.

The 152 cross-department names look like one person teaching in a related or cross-listed department, for example:

| Name | Keeper's department | Duplicates' department |
|---|---|---|
| `ALEXANDER A S` | PSY | DYNS |
| `ICHIBA T` | PSTAT | PSTATW |
| `BEGLEY M R` | ME | MATRL |
| `KOSIK K S` | MCDB | DYNS |
| `ORTEGA G` | FEMST | FEMSTW |
| `WOODS V E` | PSY | INT |

The grades loader already resolves these names to the keeper, so their grades are there already.

## Why bother

- **Pass 4 skips real pairs.** `find_duplicate_pairs` counts every row, so an abbreviated name next to two identical full-name rows looks ambiguous. That is why pass 4 skipped `KOTH M` and `BUENO CACHADI` (C2, 2026-09-29). The grade loader (PR #18) counts names rather than rows, but pass 4 doesn't.
- **WOODS can't be settled until they're gone.** `WOODS M P` has rows 15235 (keeper, MUS), 81447 (MUS) and 95409 (ED). Row 95409 makes `WOODS M` ambiguous in ED; see "WOODS" below.
- **Past-quarter data is split.** A professor's 20262/20263 sections sit on a row without their grades or ratings.
- **They block routine cleanup.** They're about 17% of the table (8,616 rows), and none of them has data of its own.

## The change

Two steps, in one maintenance window:

1. **Re-point the sections.** For every section on a duplicate row, set `professor_id` to the row's keeper. Expected: 3,323 sections.

   ```sql
   WITH k AS (
     SELECT id, min(id) OVER (PARTITION BY name_nexus) AS keeper_id
     FROM professors WHERE name_nexus IS NOT NULL
   )
   UPDATE scheduled_sections s SET professor_id = k.keeper_id
   FROM k WHERE s.professor_id = k.id AND k.id <> k.keeper_id;
   ```

   Save `(section id, old professor_id)` for all 3,323 rows to a file first, so this step can be undone without restoring a branch.

2. **Delete the now-orphaned rows with the existing script:** `python scripts/delete_orphan_professors.py`, dry run first, then `--apply` (see `docs/runbooks/delete-orphan-professors.md`). Its conditions are exactly this set:
   - no references;
   - no RMP identity;
   - an older row with the same name exists.

   Expected: 1,476 rows deleted, and professors go from 8,616 to 7,140. If the dry run finds more rows than 1,476, stop and look before applying.

This doesn't depend on PR #19. If the owner also approves the **B4 re-point of past quarters** (20262 and 20263, using the new matcher; see PR #19), that re-point already moves these 3,321 sections to the keeper, and step 1 becomes a no-op. The two can run in either order. Snapshot estimate of that re-point, stored professor vs new matcher:

| Quarter | Unchanged | Duplicate row → keeper (this plan) | To another professor | No match (auto-create) |
|---|---|---|---|---|
| 20262 | 1,763 | 2,586 | 468 | 271 (127 names) |
| 20263 | 404 | 735 | 108 | 79 (44 names) |

## Rehearsal (on a Neon branch copied from production)

1. Run steps 1 and 2. Check:
   - 3,323 sections updated;
   - 1,476 professors deleted;
   - `sections`, `grade_distributions`, `rmp_ratings` and `gaucho_scores` counts unchanged;
   - no section points at a missing professor.
2. **Stability:**
   - **Grade loader:** load the current Daily Nexus CSV with `scrapers.grades_loader.load_grades_to_db`. Expect 0 rows inserted and 0 professors created.
   - **Nightly matcher:** replay it over the branch's 20264 names. Every section must resolve to the same professor as before the change.
   - **Pass 4:** run it as a dry run (`run_enhanced_matching(..., merge_duplicates=True)` inside a rolled-back transaction). Record the pairs it would now merge, since fewer should be ambiguous, and review them separately. Don't merge them as part of this plan.
3. **API:** `/ready` and `/courses/<id>/professors` return 200 for a few affected courses, and the same professor no longer appears twice.

## Production

1. **Pick a window.** None of these writes can overlap a job, and the jobs start late:

   | Job | Scheduled (UTC) | Actual start seen |
   |---|---|---|
   | Nightly sync | 08:30 daily | 13:00–17:00 |
   | RMP refresh | Saturday 09:00 | runs until about 14:00 |
   | Backup | Sunday 06:00 | |
   | Quarterly grades | 25 Jan/Apr/Jul/Oct 10:00 | |

2. **Dry run.** Run the step 1 `SELECT` form (count of sections per quarter) and the orphan script with no flag. The counts must match the rehearsal, allowing for the nightly's changes to 20264.
3. **Backup branch.** Create `pre-same-name-dedup-YYYY-MM-DD` from `production`, with no compute.
4. **Apply.** Save the mapping file, then run step 1 in one transaction, then run the orphan script with `--apply`.
5. **Verify.** Compare before and after counts for professors, sections, grades, ratings and scores. Re-run the orphan dry run (expect 0). Check that `alembic_version` hasn't changed and that `/ready` returns 200.

## Rollback

- **Step 1 only:** re-apply the saved `(section id, old professor_id)` mapping. This needs the deleted rows back first, so after step 2 use the backup branch.
- **Everything:** restore `production` from `pre-same-name-dedup-YYYY-MM-DD` in the Neon console. This also discards anything the jobs wrote afterwards, so do it before the next nightly if at all.

## WOODS, after this plan

After step 2, `WOODS M P` is only row 15235 (MUS), and 95409's ED section points at it. Then merge `WOODS M` (101066: one EDIA321 2020 row, the same course as `WOODS M J`) into `WOODS M J` (10233, ED) with `etl.enhanced_matcher._merge_pair`, as for C2.

**Why the order matters:** once 95409 is gone, ED has only one full name for `WOODS M`, so the grade loader (PR #18) resolves the CSV's `WOODS M` rows to 10233 instead of recreating 101066. **Prove this on the rehearsal branch** by loading the CSV after the merge: expect 0 inserted and 0 created.

This merge is a separate approval.

`RAVEN M` (101052) stays unmerged. Its MCDB 126BL Winter 2015 row has different numbers from `RAVEN M A`'s, so it's another section or another instructor. Merging it would give `RAVEN M A` a second row for that course and quarter, and PR #18's conflict rule would then recreate `RAVEN M` on the next grade load.

## Not covered

- Duplicates whose names differ (abbreviated vs full). That's pass 4's job; see C2 and the dry run above.
- Rows that the B4 re-point leaves with no references but a unique name. The orphan script keeps the oldest row of every name, so they remain until a separate decision.

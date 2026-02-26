# Enhanced Professor Matching — Implementation Record

**Date:** 2026-02-26
**Status:** COMPLETE — code merged, tests passing, not yet run against production DB

## Problem

The targeted scrape (`scrapers/targeted_scrape.py`) searches RMP by name for each unmatched professor. This fails for 86% of Nexus names because they are initial-only ("HUANG L") — searching "L Huang" on RMP returns wrong/ambiguous results. Result: 19 collision errors, 0 new matches in 297 attempts.

**Root cause:** The 1,367 UCSB RMP professors are already in the DB. The problem is purely local matching — we need to match 5,458 initial-only Nexus names against those existing RMP records using last name + initial + department, not by re-searching the API.

## Solution

A 4-pass local matching engine (`etl/enhanced_matcher.py`) that runs entirely against the existing DB — no API calls.

### Pass 1 — Initial Match (~379 expected matches)
For initial-only Nexus names ("HUANG L"), find RMP professors with matching last name + first initial. Link only when exactly 1 candidate exists. Confidence: 90 (dept match) or 75 (no dept).

### Pass 2 — Full-Name Fuzzy (~50-100 expected matches)
For full-name Nexus professors still unmatched, fuzzy match (TheFuzz `token_sort_ratio`) against unlinked RMP records. Threshold: 85+. Department match boosts confidence by +5.

### Pass 3 — Department Disambiguation (~10 expected matches)
For ambiguous initial-only names (multiple RMP candidates with same last name + initial), use department mapping to narrow to exactly 1.

### Pass 4 — Nexus Deduplication (~9 expected merges)
Find duplicate Nexus professor pairs ("CHANG S" + "CHANG SHIYU" in same dept). Transfer grade records from abbreviated to full-name professor, delete the abbreviated row.

**Expected improvement:** ~400-500 new matches (973 -> ~1,370-1,470), a ~40% increase.

## Files Created

| File | Purpose |
|------|---------|
| `etl/name_utils.py` | `parse_nexus_name()`, `is_initial_only()`, `initial_matches()`, `find_duplicate_pairs()` |
| `etl/department_mapper.py` | `DEPT_MAP` (65 UCSB dept codes -> RMP names), `departments_match()` with fuzzy fallback |
| `etl/enhanced_matcher.py` | 4-pass engine: `_pass1_initial_match`, `_pass2_fullname_fuzzy`, `_pass3_dept_disambiguation`, `_pass4_deduplication`, `run_enhanced_matching()` |
| `tests/test_name_utils.py` | 14 tests — parsing, initial detection, duplicate finding |
| `tests/test_department_mapper.py` | 8 tests — exact, case-insensitive, fuzzy, multi-name depts |
| `tests/test_enhanced_matcher.py` | 8 tests — DB-backed via SAVEPOINT fixture (link, collision, pass1/2/4) |

## Files Modified

| File | Change |
|------|--------|
| `scripts/run_pipeline.py` | Added `--match` flag, `run_matching()` function between scrape and NLP phases |
| `README.md` | Updated project structure, added pipeline usage section, linked this doc |

## Key Implementation Details

### SQLAlchemy Cascade Handling
When linking a Nexus professor to an RMP-only professor, the RMP row must be deleted. SQLAlchemy's default cascade behavior tries to null-ify FKs on related `rmp_ratings` rows, but `professor_id` is NOT NULL. Solution:
1. Transfer ratings to the Nexus professor
2. Clear `rmp_id` on the RMP row (avoid unique constraint violation)
3. Flush + `session.expire(rmp_prof)` to prevent cascade
4. Delete the RMP row
5. Set `rmp_id` on the Nexus professor

Same pattern in Pass 4 (deduplication) — duplicate grades are deleted, non-duplicates transferred, then `session.expire()` before deleting the abbreviated professor.

### Department Mapping
`DEPT_MAP` covers 65 UCSB department codes mapped to their RMP equivalents. Multi-mapping supported (e.g., CHEM -> "Chemistry" OR "Chemistry And Biochemistry"). Fuzzy fallback (threshold 80) for departments not in the static map.

## Test Results

**75 tests passing** (45 existing + 30 new), 0 failures.

```
tests/test_name_utils.py        — 14 passed
tests/test_department_mapper.py — 8 passed
tests/test_enhanced_matcher.py  — 8 passed
```

## Next Steps (on laptop)

1. **Start DB:**
   ```bash
   docker compose up db -d
   ```

2. **Run enhanced matching against production data:**
   ```bash
   python scripts/run_pipeline.py --match
   ```
   Watch the logs — Pass 1-4 stats will print. Expected: ~400+ new matches.

3. **Recompute NLP + scores with new matches:**
   ```bash
   python scripts/run_pipeline.py --nlp --score
   ```

4. **Verify match count:**
   ```bash
   docker compose exec db psql -U gco -c \
     "SELECT count(*) FROM professors WHERE rmp_id IS NOT NULL AND name_nexus IS NOT NULL;"
   ```
   Should be ~1,370+ (up from 973).

5. **Re-export DB (if export script exists):**
   ```bash
   bash scripts/export_db.sh
   ```

6. **Commit the results:**
   ```bash
   git add -A && git commit -m "data: run enhanced matching pipeline"
   ```

# Plan 01-02: N+1 Fix + Scoring Tests — Summary

**Phase:** 01-foundation-bug-fixes
**Plan:** 01-02
**Executed:** 2026-03-30
**Status:** Complete

## What Was Implemented

### Task 1: Fix N+1 Query in get_professors_for_course() (FDN-03)
- `dashboard/queries.py`: Replaced 1+3N per-professor queries with 2-query approach
  - Main query: JOIN with `latest_rating_sq` and `sentiment_sq` subqueries
  - 2nd query: single `IN (rating_ids)` for keywords
  - GROUP BY: `(Professor.id, RmpRating.id)` — removed redundant `avg_sentiment` column
  - `max(id)` for latest rating (valid for sequential ETL inserts — documented inline)
- `tests/test_dashboard_queries.py`: Added `test_get_professors_returns_rmp_data`
  - Covers professor with RMP data (quality, sentiment, keywords) and without
  - Requires live DB (Neon) — expected to skip locally

### Task 2: Gaucho Score Formula Tests (TEST-02)
- `tests/test_scoring.py`: Added 10 new known-input/output tests
  - Boundary: all-zero, all-half (50.0), all-max (100.0)
  - Exact normalization: GPA 3.52→0.88, quality 4.2→0.84, difficulty 3.1→0.38
  - Full pipeline known case with equal weights
  - Bayesian adjust zero-count edge case
  - Clamping and single-weight scenarios
  - These serve as ground truth for Phase 3 client-side recomputation

## Tests
- 23/23 pass (all runnable tests)
- test_scoring.py: 16 pass (6 original + 10 new)
- test_dashboard_queries.py: requires Neon DB (will run in CI)

## Requirements Covered
- FDN-03: N+1 query eliminated ✓
- TEST-02: Gaucho Score formula verified for known inputs ✓

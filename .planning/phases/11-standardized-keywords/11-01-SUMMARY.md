---
phase: 11-standardized-keywords
plan: 01
status: complete
started: 2026-04-08
completed: 2026-04-08
---

# Plan 11-01: Standardized Keywords Backend

## What Was Built

Added a curated tag vocabulary (~15 labels across 6 categories) and a mapping function that transforms raw NLP-extracted keywords into structured, frequency-filtered tags. The API now returns `tags: [{name, count}]` instead of `keywords: [string]`.

## Key Changes

- `dashboard/queries.py` — `TAG_VOCABULARY` dict mapping ~15 substrings to curated labels, `map_keywords_to_tags()` function with frequency threshold, per-comment deduplication in `get_professors_for_course()`
- `api/schemas.py` — New `ProfessorTag` model (name + count), `ProfessorRanking.keywords` replaced with `ProfessorRanking.tags`
- `api/routers/courses.py` — Passes `tags` field from query result to API response
- `tests/test_tag_mapping.py` — 14 tests covering mapping, thresholds, dedup, structure, integration

## Test Results

14/14 backend tests passing. Zero regressions.

# Plan 01-03: Scraper Test Mocking — Summary

**Phase:** 01-foundation-bug-fixes
**Plan:** 01-03
**Executed:** 2026-03-31
**Status:** Complete

## What Was Implemented

### Task 1: Audit all test files for real HTTP calls

Audited all 19 test files. Findings:

| File | Status | Notes |
|------|--------|-------|
| test_rmp_scraper.py | SAFE | Pure parse/fixture tests; mocked test added |
| test_targeted_scrape.py | SAFE | Uses MagicMock on scraper |
| test_grades_loader.py | SAFE | Inline dict data, no HTTP |
| test_grades_ingester.py | SAFE | Reads local CSV fixture, no HTTP |
| test_integration.py | SAFE | Inline data, no HTTP |
| test_batch_nlp.py | SAFE | ETL logic, no HTTP |
| test_batch_scoring.py | SAFE | ETL logic, no HTTP |
| All others | SAFE | No HTTP calls found |

**Added:** `test_search_teacher_by_name_mocked` to `tests/test_rmp_scraper.py`:
- Uses `_load_name_search_fixture()` helper (consistent with existing pattern)
- Patches `scraper._request` via `mocker.patch.object`
- Asserts 2 results returned and `results[0]["first_name"] == "John"`
- Asserts `_request.assert_called_once_with(NAME_SEARCH_QUERY, {"text": "John Smith", "schoolID": scraper.school_id_encoded})`

### Task 2: Verify full test suite passes deterministically

- 68 non-DB tests pass; 28 DB errors are pre-existing (psycopg2 auth failure — no local Postgres)
- `grep -rn "from curl_cffi\|import curl_cffi" tests/` returns no matches
- `tests/fixtures/targeted_scrape_response.json` NOT created — test_targeted_scrape.py uses inline MagicMock data

## Tests
- test_rmp_scraper.py: 5/5 passed (including new mocked test)
- All 68 non-DB tests pass

## Requirements Covered
- TEST-01: All scraper tests use mocked HTTP; CI is fully deterministic ✓

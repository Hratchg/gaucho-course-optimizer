---
status: complete
phase: 01-foundation-bug-fixes
source: 01-01-SUMMARY.md, 01-02-SUMMARY.md
started: 2026-03-30T23:00:00Z
updated: 2026-03-30T23:00:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: From a fresh shell, run `python -c "from db.connection import get_engine, get_session_local, get_session; print('OK')"` — should print OK with no import errors or exceptions.
result: pass

### 2. Connection pool parameters
expected: Run `python -c "from db.connection import get_engine; e = get_engine(); print(e.pool.size(), e.pool._max_overflow, e.pool._recycle)"` — should print `5 10 1800`.
result: pass

### 3. SessionLocal factory export
expected: Run `python -c "from db.connection import get_session_local; s1 = get_session_local(); s2 = get_session_local(); print(s1 is s2)"` — should print `True` (same object both calls — singleton).
result: pass

### 4. FK indexes migration file
expected: Run `grep -c "create_index" db/migrations/versions/*fk_indexes*` — should return 6. Run `grep "down_revision" db/migrations/versions/*fk_indexes*` — should show `'3ee0c9e2add3'`.
result: pass

### 5. RMP auth token fails loudly
expected: Run `python -c "import os; os.environ.pop('RMP_AUTH_TOKEN', None); from scrapers.rmp_scraper import RmpScraper; RmpScraper()"` — should raise `KeyError: 'RMP_AUTH_TOKEN'`, not a silent failure or default token.
result: pass

### 6. No hardcoded RMP token in source
expected: Run `grep "dGVzdDp0ZXN0" scrapers/rmp_scraper.py` — should return no matches (exit code 1 / empty output).
result: pass

### 7. N+1 query fix — test suite passes
expected: Run `pytest tests/test_scoring.py tests/test_rmp_scraper.py tests/test_db_connection.py -v` — all tests should pass (16 + 4 + 4 = 24 tests).
result: pass

### 8. Gaucho Score formula tests — known inputs
expected: Run `pytest tests/test_scoring.py -v -k "known"` — the known-input tests (all-zero → 0.0, all-max → 100.0, equal weights) should pass.
result: pass

### 9. avg_sentiment zero value preserved
expected: Run `python -c "avg = 0.0; result = round(float(avg), 2) if avg is not None else None; print(result)"` — should print `0.0`, not `None`.
result: pass

## Summary

total: 9
passed: 9
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none yet]

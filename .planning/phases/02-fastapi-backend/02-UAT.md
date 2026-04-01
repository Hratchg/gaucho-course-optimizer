---
status: partial
phase: 02-fastapi-backend
source:
  - 02-01-SUMMARY.md
  - 02-02-SUMMARY.md
  - 02-03-SUMMARY.md
  - 02-04-SUMMARY.md
  - 02-05-SUMMARY.md
started: 2026-03-31T21:00:00Z
updated: 2026-03-31T21:00:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: |
  Kill any running server/service. Clear ephemeral state (temp DBs, caches, lock files).
  Start the application from scratch with: uvicorn api.main:app --reload
  Server boots without errors, and a health check returns live data:
  curl http://localhost:8000/health  → {"status": "ok"}
result: pass

### 2. Health Endpoint
expected: |
  GET /health returns HTTP 200 and body {"status": "ok"}.
  No database connection required — endpoint has no Depends(get_db).
result: pass

### 3. Course Search — Returns Results
expected: |
  GET /courses/search?q=CMPSC returns HTTP 200 and a JSON array of courses.
  Each item has at least: code, title, department fields.
  Results match the query (courses with "CMPSC" in code or title appear).
result: blocked
blocked_by: neon-schema-not-initialized
reason: "Neon database only has alembic_version table — courses/professors/etc schema not applied. API routes 500 with 'relation courses does not exist'."

### 4. Course Search — Input Validation
expected: |
  GET /courses/search?q=physics$123 returns HTTP 422 (special character $ rejected).
  GET /courses/search?q=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA (101 A's) returns HTTP 422 (max_length=100 exceeded).
result: pass

### 5. Professor Ranking for Course
expected: |
  GET /courses/{course_id}/professors for a course that has professors returns HTTP 200.
  Response is a JSON array sorted by gaucho_score descending.
  Each item has fields: gaucho_score, gpa_factor, quality_factor, difficulty_factor, sentiment_factor.
  GET /courses/999999/professors (unknown course) returns HTTP 404.
result: blocked
blocked_by: neon-schema-not-initialized
reason: "Neon database has no schema — data tables do not exist."

### 6. Grade Distribution
expected: |
  GET /professors/{prof_id}/grades?course_id={course_id} returns HTTP 200.
  Response is a list with quarter, avg_gpa, a_plus, a, ..., f fields.
  GET /professors/{prof_id}/grades (no course_id) returns HTTP 422.
  GET /professors/999999/grades?course_id=1 returns HTTP 404.
result: blocked
blocked_by: neon-schema-not-initialized
reason: "Neon database has no schema — data tables do not exist."

### 7. Professor Comments
expected: |
  GET /professors/{prof_id}/comments returns HTTP 200.
  Response is a list of comments with text, sentiment_score (raw VADER float in [-1,1]), keywords, created_at fields.
  GET /professors/{prof_id}/comments?limit=2 returns at most 2 results.
  GET /professors/999999/comments returns HTTP 404.
result: blocked
blocked_by: neon-schema-not-initialized
reason: "Neon database has no schema — data tables do not exist."

### 8. Automated Test Suite Passes
expected: |
  Running: python -m pytest -v
  All 129 tests pass (0 failures, 0 errors).
  tests/test_api/ shows 13 passing tests.
  No "ERROR" lines in output.
result: pass

## Summary

total: 8
passed: 4
issues: 0
pending: 0
skipped: 0
blocked: 4

## Gaps

[none yet]

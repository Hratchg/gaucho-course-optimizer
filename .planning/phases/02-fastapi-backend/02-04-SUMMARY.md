---
phase: 02-fastapi-backend
plan: 04
status: complete
commit: 1bfd4c7d5c285d4209c3a836b4da6f220f573bec
---

# Plan 02-04 Summary: Professors Router

## What Was Built

Replaced stub `api/routers/professors.py` with GET /professors/{id}/grades and GET /professors/{id}/comments — direct wrappers around dashboard/queries.py functions with no score computation.

## Endpoints

### GET /professors/{id}/grades?course_id={cid}
- `course_id` is REQUIRED (Query `...`) — 422 if omitted
- Returns `list[GradeQuarter]` with per-quarter grade distribution
- 404 when no grade data found

### GET /professors/{id}/comments
- `limit` defaults to 5, bounds ge=1, le=50
- Returns `list[CommentResult]` with raw VADER sentiment_score ([-1,1], NOT re-normalized)
- 404 when no comments found

## Files Changed

| File | Change |
|---|---|
| `api/routers/professors.py` | Stub → full implementation |
| `tests/test_professors_router.py` | 7 tests with TestClient + try/finally cleanup |

## Tests

7/7 passing. Includes: 422 on missing course_id, 404 on empty results, limit forwarding verification, raw VADER passthrough assertion.

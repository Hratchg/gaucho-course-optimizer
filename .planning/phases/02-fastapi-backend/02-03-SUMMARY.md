---
phase: 02-fastapi-backend
plan: 03
status: complete
commit: 394674973cd2257581ef7312efe361a3c2a57376
---

# Plan 02-03 Summary: Courses Router

## What Was Built

Replaced the stub `api/routers/courses.py` with full implementations of GET /courses/search and GET /courses/{course_id}/professors. Extended dashboard/queries.py to search by both course code and title.

## Endpoints

### GET /courses/search
- Query param `q`: min_length=1, max_length=100, pattern `^[a-zA-Z0-9 \-]+$`
- Returns `list[CourseResult]` (up to 20 results)
- 422 on invalid input (special chars, too long, empty)

### GET /courses/{course_id}/professors
- Returns `list[ProfessorRanking]` sorted by gaucho_score descending
- Scores computed fresh per-request (not from gaucho_scores table)
- VADER normalization: `(avg_sentiment + 1) / 2` maps [-1,1] → [0,1]
- None-safe fallbacks: all normalize_* calls default to 0.5
- 404 when no professors found for course_id
- Passthrough fields: std_gpa, avg_sentiment, match_confidence included in response

## Files Changed

| File | Change |
|---|---|
| `api/routers/courses.py` | Stub → full implementation |
| `dashboard/queries.py` | search_courses() extended to search both code AND title via or_() |
| `tests/test_courses_router.py` | 9 tests: 422 validation, 404, VADER normalization, None fallbacks, route order, passthrough fields |

## Tests

9/9 passing. All using TestClient + dependency_overrides with try/finally cleanup.

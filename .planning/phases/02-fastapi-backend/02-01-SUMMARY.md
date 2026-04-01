---
phase: 02-fastapi-backend
plan: 01
status: complete
commit: 60e51e725fd5894b7e67e5b9b69f866e6951364e
---

# Plan 02-01 Summary: N+1 Bulk JOIN Rewrite

## What Was Built

Rewrote `compute_all_scores()` in `etl/scoring.py` from a 3-queries-per-professor N+1 loop (~35,250 queries for 11,750 pairs) to a single bulk JOIN query. This closes FDN-03 and unblocks all Wave 2 API work.

## Implementation

- **Subquery 1** (`latest_rating_sq`): `MAX(id)` per professor — selects latest RmpRating row
- **Subquery 2** (`sentiment_sq`): `AVG(sentiment_score)` per rmp_rating_id — aggregates comments
- **Single bulk JOIN**: professors + grade_distributions + latest RMP + avg sentiment in one round trip
- **Python-side scoring**: normalize → bayesian adjust → compute_gaucho_score per row
- **Upsert**: DELETE + INSERT per `(professor_id, course_id)` + one `session.commit()`

## Tests

20/20 pass (0.18s). 4 new integration tests added using SQLite in-memory fixture (`mem_session`):
- `test_compute_all_scores_returns_computed` — computed > 0, skipped == 0
- `test_compute_all_scores_skips_professor_with_null_quality` — null quality → skipped
- `test_compute_all_scores_no_duplicates_on_second_call` — upsert idempotency
- `test_compute_all_scores_return_dict_always_has_both_keys` — both keys always present

## Files Changed

| File | Change |
|---|---|
| `etl/scoring.py` | compute_all_scores() rewritten; removed time.sleep, get_engine().dispose, batch-session loop |
| `tests/test_scoring.py` | 4 integration tests added |
| `tests/conftest.py` | python-dotenv auto-load (override=False, CI-safe) |
| `db/models.py` | UniqueConstraint added to GauchoScore(professor_id, course_id) |

## Follow-on

`UniqueConstraint("professor_id", "course_id", name="uq_gaucho_score_pair")` is in the model but not yet applied to the Neon database. Apply via `ALTER TABLE gaucho_scores ADD CONSTRAINT uq_gaucho_score_pair UNIQUE (professor_id, course_id)` when alembic migrations are wired up in Phase 2.

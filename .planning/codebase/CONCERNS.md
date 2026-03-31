# Codebase Concerns

**Analysis Date:** 2026-03-30

## Technical Debt

| Area | Issue | Severity | File(s) |
|------|-------|----------|---------|
| Database connections | No connection pooling configured; `get_session()` creates unbounded sessionmakers | High | `db/connection.py` |
| Error handling | Broad `except Exception` catches without specific error types; errors logged but not surfaced to user | High | `scrapers/targeted_scrape.py`, `scheduler/jobs.py` |
| Hardcoded auth | Default base64-encoded auth token `dGVzdDp0ZXN0` shipped in code; credentials not environment-isolated | High | `scrapers/rmp_scraper.py` (line 105) |
| N+1 queries | RMP rating fetched per professor in loop; each professor lookup is a separate query | Medium | `dashboard/queries.py` (lines 45-49) |
| Missing input validation | Course search accepts raw user input without escaping; SQL injection risk via `ilike()` | Medium | `dashboard/queries.py` (line 19) |
| Sentiment analysis fallback | Returns 0.0 for any parse error, masking actual sentiment; comments without text treated as neutral | Low | `etl/nlp_processor.py` (lines 15-19) |
| Session lifecycle | Sessions created per-request in dashboard; not reused or pooled | Medium | `dashboard/app.py` (lines 45-71) |

## Known Bugs / TODOs

- `README.md:19` — TODO: Add dashboard screenshots (not blocking, documentation)
- `etl/nlp_processor.py:80-82` — Keywords stored only on first comment per rating; if multiple ratings exist for same professor, some keyword data is orphaned
- `scrapers/rmp_loader.py:112` — Session always commits after every teacher load; no transaction batching for bulk imports

## Security Considerations

| Concern | Location | Risk |
|---------|----------|------|
| Hardcoded RMP auth token | `scrapers/rmp_scraper.py:105` | High — Default token `dGVzdDp0ZXN0` (base64 "test:test") is a dummy credential; if real credentials exist in production .env, accidental commit is possible |
| No input validation in search | `dashboard/queries.py:19` | Medium — `ilike()` query could be vulnerable to SQL injection if user input bypassed; `%query%` pattern allows wildcard-based DoS with slow patterns |
| Unencrypted database URL in env | `db/connection.py:11`, `tests/conftest.py:6` | Medium — DATABASE_URL may contain credentials; requires careful .env handling |
| No authentication on dashboard | `dashboard/app.py` | Low — Dashboard is public; no login/authorization required; acceptable for internal UCSB tool but risky if exposed externally |
| Missing CORS/CSRF | All | Low — Single-origin dashboard, but if API endpoints added later, no CSRF protection exists |

## Performance Bottlenecks

| Concern | Location | Impact |
|---------|----------|--------|
| Linear RMP queries per professor | `dashboard/queries.py:45-49` | High — O(n) additional queries; 100 professors = 100 separate RMP rating fetches. Should use eager loading or JOINs |
| Sentiment extraction on every comment | `etl/nlp_processor.py:63-65` | Medium — VADER analyzer created fresh per process; no caching. For 10k comments, this is repeated work |
| TF-IDF vectorizer created per rating | `etl/nlp_processor.py:36` | Medium — Full vectorizer built per rating_id even if comments are similar; should batch across all professors |
| No database indexes on foreign keys | `db/models.py` | Medium — No explicit indexes on professor_id, course_id, rmp_rating_id lookups; sequential scans possible on large tables |
| Streamlit cache keyed by function args only | `dashboard/app.py:44-72` | Low — Stale cache if weights change between calls; works but inefficient for dynamic scoring |

## Fragile Areas

Areas likely to break under change:

- `etl/enhanced_matcher.py` (420 lines) — Complex multi-pass matching logic with mutual state dependencies (Pass 2 depends on Pass 1 output). Tests exist but modifying any pass requires re-validating collision guards and deduplication.
  - Files: `etl/enhanced_matcher.py`
  - Fragility reason: Four sequential passes modify database state; removing professor records mid-pipeline risks cascading failures
  - Safe modification: Add integration tests verifying all passes together, not just individual pass tests
  - Test coverage: Unit tests exist for each pass (`tests/test_enhanced_matcher.py`); missing end-to-end collision testing

- `etl/name_matcher.py` + `etl/name_utils.py` — Fuzzy matching thresholds (70, 85) are magic numbers without tuning documentation
  - Files: `etl/name_matcher.py`, `etl/name_utils.py`, `etl/enhanced_matcher.py`
  - Fragility reason: Thresholds hardcoded; changing one breaks match confidence assumptions across multiple passes
  - Safe modification: Extract thresholds to config file or constants module
  - Test coverage: Good (`tests/test_enhanced_matcher.py`, `tests/test_name_utils.py`), but no threshold sensitivity analysis

- `dashboard/queries.py:43-86` — Multiple separate queries per professor construct final data structure
  - Files: `dashboard/queries.py`
  - Fragility reason: Adding new fields requires adding new queries; no central query builder
  - Safe modification: Refactor to single aggregated query or use SQLAlchemy eager loading
  - Test coverage: Integration tests exist (`tests/test_dashboard_queries.py`), but high latency not measured

- `db/models.py` relationships and cascades
  - Files: `db/models.py`
  - Fragility reason: No cascade directives defined; deleting Professor doesn't cascade to grades/ratings/scores. Manual cleanup required or orphans accumulate
  - Safe modification: Add `cascade="all, delete"` to relationship definitions OR add cleanup migrations
  - Test coverage: No explicit cascade tests

## Missing Infrastructure

- [ ] Database connection pooling — `db/connection.py` creates new sessionmakers per call; pool_size/max_overflow not set
- [ ] Explicit cascade delete rules — Deleting a professor leaves orphaned grade/RMP/score records
- [ ] Request-scoped session management — Dashboard creates new sessions per function; no session cleanup on exception
- [ ] Input validation middleware — No schema validation before database queries
- [ ] Rate limiting on RMP scraper — Delay is random (2-4s) but unbounded; no backoff on 429/403 responses
- [ ] Database indexes on foreign keys — No explicit indexes on `professor_id`, `course_id`, `rmp_rating_id` columns
- [ ] Batch insert/update — Grade loading and RMP loading insert row-by-row; no bulk operations
- [ ] Sentiment sentiment caching — VADER analyzer rebuilt per call; no LRU cache
- [ ] Data quality validation — No checks for NULL avg_gpa, missing RMP data, stale data before scoring
- [ ] Query performance logging — No slow query tracking; N+1s not visible

## Recommendations

Priority improvements before adding new features:

1. **Fix N+1 query in dashboard queries (High)** — `dashboard/queries.py:43-86` currently loops over professors fetching RMP data one-by-one. Refactor to use `joinedload()` or single aggregated query. Impact: Dashboard will be 10-100x faster for courses with many professors. Effort: 2-3 hours.

2. **Add database connection pooling (High)** — `db/connection.py:12` should set `pool_size=10, max_overflow=20` and enable `pool_recycle=3600`. Prevents "too many connections" errors in production. Effort: 30 minutes.

3. **Extract hardcoded thresholds and credentials to config (High)** — Move fuzzy match thresholds (70, 85), RMP school_id (1077), auth_token, and database URLs to environment variables or config file. Reduces accidental credential leaks. Effort: 1 hour.

4. **Add explicit database indexes (Medium)** — Create indexes on `professor_id`, `course_id`, `rmp_rating_id` foreign key columns in migration. Query planner will use these instead of sequential scans. Effort: 30 minutes.

5. **Implement specific exception handling (Medium)** — Replace `except Exception` with `except (HTTPError, TimeoutError, ValueError)` in `scrapers/targeted_scrape.py` and `scheduler/jobs.py`. Surface errors to monitoring/alerting. Effort: 1 hour.

6. **Add cascade delete rules (Medium)** — Define `cascade="all, delete"` in `db/models.py` relationships or add cleanup job. Prevents orphaned records. Effort: 1 hour.

7. **Batch RMP and grade loading (Low)** — Replace row-by-row inserts with `session.bulk_insert_mappings()`. Reduces time for large imports. Effort: 2 hours.

8. **Add query performance monitoring (Low)** — Log slow queries using SQLAlchemy event listeners. Identify future bottlenecks. Effort: 1 hour.

---

*Concerns audit: 2026-03-30*

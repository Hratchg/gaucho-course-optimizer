# Domain Pitfalls

**Domain:** React + FastAPI student web app wrapping existing Python ETL pipeline
**Project:** Gaucho Course Optimizer
**Researched:** 2026-03-30

---

## Critical Pitfalls

Mistakes that cause rewrites, data loss, or hard-to-diagnose production failures.

---

### Pitfall 1: SQLAlchemy Session Shared Between FastAPI Request and APScheduler Job

**What goes wrong:** The existing codebase creates sessions at module/function scope in `dashboard/app.py` rather than per-request. When FastAPI is added, the temptation is to pass the same session to APScheduler background jobs. The HTTP request finishes, FastAPI closes the session via its dependency context manager, and the scheduled job then tries to use a permanently-closed session — failing with `sqlalchemy.exc.InvalidRequestError: This Session has been permanently closed`.

**Why it happens:** APScheduler jobs run in a thread pool outside FastAPI's request lifecycle. FastAPI's `Depends(get_db)` generator closes the session in its `finally` block when the request handler returns. Any object that captured the session reference is now holding a closed session.

**Consequences:** Nightly RMP scraper and quarterly grade refresh jobs silently fail or throw cryptic errors. Data stops refreshing. The APScheduler in `scheduler/jobs.py` uses the same session infrastructure currently shared with the dashboard.

**Warning signs:**
- `InvalidRequestError: Session is already closed` in scheduler logs
- Scheduled jobs succeed locally (where sessions are not request-scoped) but fail on Render
- `DetachedInstanceError` when scheduler tries to access ORM objects loaded in a previous request

**Prevention:** APScheduler jobs must create and close their own sessions independently from FastAPI's request lifecycle. Use a `sessionmaker` factory directly in each job function:
```python
# scheduler/jobs.py — each job creates its own session
def run_rmp_refresh():
    with SessionLocal() as session:
        # all work inside this block
        ...
```
Never pass a session from a FastAPI dependency into a scheduler job.

**Phase:** Must be addressed in the FastAPI setup phase, before wiring scheduler to the new API layer.

---

### Pitfall 2: SQLAlchemy Lazy Loading Triggers DetachedInstanceError After Session Closes

**What goes wrong:** FastAPI serializes Pydantic response models after the endpoint function returns. If a Pydantic schema has `from_attributes=True` (formerly `orm_mode`) and references a relationship on a SQLAlchemy model, Pydantic will try to access that attribute during serialization. If the session is already closed (or the response model runs in a different thread), SQLAlchemy raises `DetachedInstanceError` — the ORM object is no longer bound to a live session.

**Why it happens:** The existing `dashboard/queries.py` uses separate queries per professor (N+1 pattern). When these queries are lifted into FastAPI endpoints, the session scope does not automatically extend to the Pydantic serialization step. Relationships that were not eagerly loaded cannot be accessed outside the session context.

**Consequences:**
- API endpoints return 500 errors that look like serialization failures
- The error is non-obvious: the query succeeded, but serialization failed silently
- This is the #1 reported FastAPI + SQLAlchemy bug in production

**Warning signs:**
- `DetachedInstanceError: Instance <Professor> is not bound to a Session` in API logs
- Endpoints work in tests (where session scope is wider) but fail in production
- `MissingGreenlet` errors if async SQLAlchemy is used without proper eager loading

**Prevention:**
1. Always eager-load relationships you plan to serialize. Use `joinedload()` or `selectinload()` in the query, not lazy access after the fact.
2. Do not include relationship fields in Pydantic schemas unless they are explicitly loaded.
3. For the professor ranking endpoint, the existing N+1 pattern in `dashboard/queries.py:43-86` must be refactored to a single joined query before wrapping in FastAPI — not after.

**Phase:** Bug-fix phase (fix N+1 queries first), then FastAPI setup phase.

---

### Pitfall 3: FastAPI Sync Endpoint + Sync SQLAlchemy Blocks the Threadpool — Connection Pool Exhaustion

**What goes wrong:** FastAPI runs synchronous `def` endpoints in a threadpool (anyio default: 40 threads). Each thread holds a SQLAlchemy session open while it executes. If connection pool size is smaller than threadpool size (or pool is unbounded), and requests pile up, SQLAlchemy raises `QueuePool limit of size X overflow Y reached`. Worse: the `finally` block in the `get_db` generator cannot run while all threadpool threads are blocked, so sessions never release — deadlock.

**Why it happens:** The codebase currently has no connection pooling configured (`db/connection.py` creates unbounded sessionmakers). This is marked High severity in CONCERNS.md but not yet fixed. Under any sustained traffic, this will exhaust PostgreSQL's connection limit.

**Consequences:** Full API deadlock under moderate load. On Render free tier, PostgreSQL allows ~25 connections by default. With 40 threadpool workers each holding one session, the pool runs dry almost immediately under load.

**Warning signs:**
- `QueuePool limit of size X overflow Y reached, connection timed out` in logs
- API becomes totally unresponsive (not just slow) under concurrent requests
- This condition cannot be reproduced with sequential test requests — only concurrent

**Prevention:**
1. Fix connection pooling before the FastAPI endpoint is built: `pool_size=5, max_overflow=10, pool_recycle=1800` — keep below Render's connection limit.
2. Set `pool_pre_ping=True` to detect stale connections after Render cold starts.
3. Consider `pool_timeout=10` to fail fast rather than hang indefinitely.

**Phase:** Bug-fix phase. Must be resolved before any load testing.

---

### Pitfall 4: Render Free Tier — PostgreSQL Database Deleted After 30 Days

**What goes wrong:** Render's free PostgreSQL tier now expires after **30 days** (changed from 90 days as of 2024-05-20). The database is deleted automatically. All scraped grade data, RMP data, professor matches, and Gaucho Scores are lost. The ETL pipeline must be re-run from scratch.

**Why it happens:** Render made this change to reduce infrastructure costs. Free-tier databases are not considered production resources by Render's terms.

**Consequences:** For a student project running the full ETL pipeline (Daily Nexus scrape + RMP scrape + matching + NLP + scoring), data reconstruction takes hours. If a student discovers this on registration day, the app is dead.

**Warning signs:**
- Render dashboard shows database expiry date in the service panel
- No warning email before deletion (not guaranteed)
- App returns 500 or empty results after 30 days

**Prevention:**
1. Set a calendar reminder to recreate or upgrade the database before day 30.
2. Export a `pg_dump` of the production database weekly using a scheduled script or GitHub Action.
3. Alternatively, use Neon (free tier, no expiry) or Supabase (free tier, no expiry) as the PostgreSQL host and connect Render's FastAPI service to the external DB via `DATABASE_URL`. This avoids the 30-day limit entirely.
4. Store the `pg_dump` in GitHub or S3 so the ETL pipeline can be seeded from backup without re-scraping.

**Phase:** Deployment planning phase. Decision must be made before first production deploy.

---

### Pitfall 5: Render Free Tier — 15-Minute Inactivity Sleep + 30–60s Cold Start

**What goes wrong:** Render spins down free web services after 15 minutes of inactivity. The next request triggers a cold start. For a FastAPI app with SQLAlchemy, this cold start involves: process spin-up, Python import time, SQLAlchemy engine initialization, and connection pool establishment. For UCSB students hitting the app between classes, every first request after inactivity takes 30–60 seconds — the browser may display a blank page or timeout.

**Why it happens:** Render's free tier is not designed for always-on availability. The 15-minute threshold is fixed and not configurable on the free plan.

**Consequences:**
- First visitor after dormancy period waits 30–60 seconds with no feedback
- React frontend shows a spinner indefinitely unless the loading state is explicitly handled
- CORS preflight requests (`OPTIONS`) may also cold-start the server, adding another round trip

**Warning signs:**
- Requests that take under 100ms in dev take 30+ seconds on first hit in production
- Render logs show "Starting service" messages

**Prevention:**
1. Build a loading state in the React frontend that shows "Waking up the server..." after 3 seconds of waiting. Students will understand "free hosting" if told.
2. Use a free ping service (UptimeRobot, Cron-job.org) to hit the API `/health` endpoint every 10 minutes. This keeps the service warm during UCSB registration peaks.
3. Add a dedicated `/health` endpoint in FastAPI that returns `{"status": "ok"}` immediately — no DB query — so the ping cost is minimal.
4. Set `pool_pre_ping=True` in SQLAlchemy so the first real DB query after cold start re-establishes the connection cleanly instead of failing.

**Phase:** FastAPI setup phase (health endpoint), React phase (loading state). Ping service setup at deployment.

---

### Pitfall 6: CORS Misconfiguration — Wildcard with Credentials, or Origin Mismatch

**What goes wrong:** Two common failure modes:
1. `allow_origins=["*"]` combined with any cookie or `Authorization` header — browsers reject this combination by spec. Even though this app has no auth, headers like `Content-Type: application/json` on non-simple requests trigger preflight, and if `allow_origins=["*"]` is set, the preflight may succeed but the actual request fails depending on browser/header combination.
2. Vercel preview deployments get random URLs (`https://gaucho-course-optimizer-abc123.vercel.app`). The FastAPI CORS config lists only the production domain. Every preview deploy fails CORS.

**Why it happens:** FastAPI's `CORSMiddleware` compares the exact origin string. `http://localhost:3000` and `http://127.0.0.1:3000` are different origins. Vercel preview URLs are unique per commit.

**Consequences:** API calls silently fail in the browser with `CORS policy: No 'Access-Control-Allow-Origin' header` — no useful error in FastAPI logs because the browser blocks the request before it processes. Developers spend hours suspecting backend bugs.

**Warning signs:**
- Browser devtools shows `Access-Control-Allow-Origin` header missing or mismatched
- API works fine with `curl` or Postman but not from the browser
- Works in dev (`localhost`) but fails in production (Vercel URL)

**Prevention:**
1. Read CORS origins from an environment variable: `ALLOWED_ORIGINS=https://gaucho-course-optimizer.vercel.app,http://localhost:5173`. This allows adding Vercel preview URLs without code changes.
2. For Vercel, use the `VERCEL_URL` variable in a custom build hook or allow the `*.vercel.app` pattern during development.
3. Place `CORSMiddleware` as the first middleware added to the FastAPI app — before any auth or error handlers.
4. In development, allow `http://localhost:5173` (Vite default) not `http://localhost:3000` (CRA default).

**Phase:** FastAPI setup phase. Must be verified before React integration.

---

### Pitfall 7: Vite Environment Variable Baked Into Build — Wrong API URL in Production

**What goes wrong:** Vite's `VITE_*` variables are replaced at **build time**, not runtime. If `VITE_API_URL` is set to `http://localhost:8000` in a `.env` file and the Vercel build runs without overriding it, the production React bundle makes requests to localhost — returning network errors for every user.

**Why it happens:** Unlike server-side environment variables, Vite substitutes `import.meta.env.VITE_API_URL` with the literal string during `vite build`. The `.env` file in the repository almost certainly contains a local dev value.

**Consequences:** Production app silently fails all API calls. The requests succeed from `curl` to the Render backend but every browser request goes to `localhost:8000` which does not resolve.

**Warning signs:**
- Browser devtools shows requests going to `http://localhost:8000` in the production app
- No errors in Render logs (because no requests arrive)
- App shows loading state forever in production but works in dev

**Prevention:**
1. Set `VITE_API_URL` as an environment variable in Vercel's dashboard under "Environment Variables" — not in any committed `.env` file.
2. Add `.env.production` to `.gitignore` if it contains real values.
3. Create a runtime check in the React app: if `import.meta.env.VITE_API_URL` is `undefined` or contains `localhost` while `window.location.hostname` is not localhost, throw a loud error at startup.

**Phase:** React setup phase and deployment phase.

---

## Moderate Pitfalls

Mistakes that cause confusion, debugging time, or degraded functionality but not total failure.

---

### Pitfall 8: pytest SAVEPOINT Pattern Breaks When FastAPI TestClient is Introduced

**What goes wrong:** The existing `db_session` fixture (SAVEPOINT pattern in `tests/conftest.py`) works correctly for direct function tests. When FastAPI's `TestClient` is introduced, it runs the app in a separate WSGI/ASGI thread. The `get_db` dependency inside the running FastAPI app creates a new session — not the test's SAVEPOINT session. Test data inserted via the fixture is not visible to the FastAPI app, and vice versa.

**Why it happens:** `TestClient` spawns the app in its own execution context. The dependency injection system creates a fresh session from the engine, bypassing the test fixture's session.

**Consequences:** FastAPI endpoint tests appear to pass (returns 200) but return empty data because the test database has no data from the fixture's perspective. Or tests insert data but the API can't see it. Very confusing to diagnose.

**Warning signs:**
- `GET /courses` returns empty list even though the test inserts a course
- Tests pass locally with mocked data but fail when testing actual DB queries via the API

**Prevention:**
Use `app.dependency_overrides` to replace `get_db` with a function that yields the test's fixture session:
```python
@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```
This ensures the TestClient's endpoint uses the same SAVEPOINT session as the test.

**Phase:** FastAPI setup phase, when first endpoint tests are written.

---

### Pitfall 9: ETL Pipeline End-to-End Test Hits Real External Services Without Mocking

**What goes wrong:** `test_integration.py` currently tests the pipeline by calling functions that load data — but the existing scraper functions make real HTTP calls to Rate My Professors and Daily Nexus. If an end-to-end test is written that calls `run_rmp_scraper()` directly, it will make live network requests in CI, hitting RMP's rate limits, possibly getting the IP blocked, and making tests non-deterministic (they depend on external availability).

**Why it happens:** The existing codebase has no HTTP mock fixtures for scrapers. `pytest-mock` is installed but not used for scraper tests (`TESTING.md` notes: "Not heavily used in this codebase — scraper tests test real HTTP calls or use fixture responses").

**Consequences:**
- CI pipeline fails non-deterministically
- RMP IP block disrupts real scraping jobs
- Tests are slow (2-4s delay per RMP request, multiplied across test cases)

**Warning signs:**
- Tests pass locally but fail in GitHub Actions (no network access or different IP)
- 429 or 403 errors appearing in test output
- Test suite takes >60s because of HTTP calls

**Prevention:**
1. Use `pytest-mock` to patch `requests.Session.send` or `httpx.Client.send` for all scraper tests.
2. Create fixture JSON files with sample RMP API responses in `tests/fixtures/`.
3. Separate unit tests (no I/O) from integration tests (real DB, mocked HTTP) from true E2E tests (real everything, manual only).
4. Add `@pytest.mark.integration` markers and exclude them from CI by default: `pytest -m "not integration"`.

**Phase:** Testing phase.

---

### Pitfall 10: SQL Injection via ilike() — Must Fix Before Public API Exposure

**What goes wrong:** `dashboard/queries.py:19` passes raw user input into an `ilike()` query as `%query%`. While SQLAlchemy's `ilike()` does parameterize the value (preventing classic SQL injection), it does not prevent wildcard-based DoS: a user searching for `%a%b%c%d%e%f%g%h%` creates an O(n^k) pattern-matching operation that can bring PostgreSQL to its knees on large datasets.

**Why it happens:** The Streamlit dashboard was internal. There was no adversarial input concern. Making this endpoint public changes the threat model entirely.

**Consequences:**
- A single malicious search string can cause the Render free-tier PostgreSQL instance to spike CPU and timeout
- The entire app becomes unresponsive for legitimate users
- Render may terminate the service for resource abuse

**Warning signs:**
- Slow query logs show `LIKE '%a%b%c%d%'` taking >5s
- CPU spike on Render after a specific search

**Prevention:**
1. Add input length validation in the FastAPI endpoint: reject queries over 100 characters.
2. Add a character allowlist or strip characters that have no meaning in a course name (keep alphanumeric, space, hyphen).
3. Add a `LIMIT` clause in the search query so a wildcard match cannot return an unbounded result set.
4. Add a database index on the course name column — even with `LIKE '%x%'`, the index won't help, but limiting the result set will.

**Phase:** Bug-fix phase, before the search endpoint is exposed publicly.

---

### Pitfall 11: No Database Indexes — Queries Degrade Silently as Data Grows

**What goes wrong:** `db/models.py` has no explicit indexes on foreign key columns (`professor_id`, `course_id`, `rmp_rating_id`). On small datasets (dozens of professors), sequential scans are fast enough to hide this. As the database grows to hundreds of professors and thousands of grade records, the N+1 query pattern in `dashboard/queries.py` compounds — each of the 100 sub-queries does a sequential scan.

**Why it happens:** SQLAlchemy does not automatically create indexes on foreign keys (unlike some ORMs). The schema was designed for a small single-user Streamlit tool.

**Consequences:**
- API endpoint for professor rankings degrades from <100ms to 5-10s as data grows
- Render's free-tier PostgreSQL CPU spikes on every course search
- Symptoms appear only with production-scale data, not in tests using 3-5 fixture rows

**Warning signs:**
- `EXPLAIN ANALYZE` output shows `Seq Scan` on large tables
- Course search gets slower over time without code changes

**Prevention:**
Create explicit indexes in an Alembic migration (or `Base.metadata.create_all` for non-migration approach):
```python
# In db/models.py
__table_args__ = (
    Index('ix_grade_dist_professor_id', 'professor_id'),
    Index('ix_grade_dist_course_id', 'course_id'),
)
```
Add indexes on all foreign keys before the first production deploy. The effort is 30 minutes per CONCERNS.md.

**Phase:** Bug-fix phase.

---

### Pitfall 12: Hardcoded RMP Auth Token Committed to Git

**What goes wrong:** `scrapers/rmp_scraper.py:105` contains a hardcoded base64-encoded auth token `dGVzdDp0ZXN0`. Even if this is a dummy placeholder, the pattern of having credentials in source code means the actual RMP token (which must exist somewhere for the scraper to work) may also be checked in, or developers will habitually add it to source code when wiring up the production Render environment.

**Why it happens:** The credential was embedded during initial development. The project has no `.env` convention enforced yet.

**Consequences:**
- Real RMP credentials committed to a public GitHub repo
- GitHub secret scanning flags the repo
- RMP account banned if token is real and exposed

**Warning signs:**
- `.env` file is not in `.gitignore`
- `os.environ.get("RMP_TOKEN", "dGVzdDp0ZXN0")` pattern — hardcoded fallback is a real credential

**Prevention:**
1. Move the token to an environment variable with no fallback: `os.environ["RMP_TOKEN"]` — fail loudly if not set.
2. Verify `.env` is in `.gitignore` before the first `git push`.
3. Add a pre-commit hook or GitHub Actions secret scanning check.
4. Set `RMP_TOKEN` in Render's environment variable dashboard, never in code.

**Phase:** Bug-fix phase, must be resolved before public repository or production deploy.

---

## Minor Pitfalls

---

### Pitfall 13: VADER Sentiment Analyzer Rebuilt Per Call

**What goes wrong:** `etl/nlp_processor.py` constructs a `SentimentIntensityAnalyzer()` object on every call to `analyze_sentiment()`. The VADER lexicon file is loaded from disk each time. For a batch operation over thousands of comments, this adds measurable wall-clock time.

**Warning signs:** `process_all_comments()` is noticeably slower than expected relative to comment count.

**Prevention:** Instantiate `SentimentIntensityAnalyzer()` once at module load time or use `functools.lru_cache` on a factory function. One line fix, high-value for batch runs.

**Phase:** Bug-fix phase.

---

### Pitfall 14: No Cascade Deletes — Orphaned Records Accumulate on Re-Scrape

**What goes wrong:** If a professor is deleted (e.g., re-running the ETL pipeline from scratch, or removing a bad match), their associated `GradeDistribution`, `RmpRating`, `RmpComment`, and `GauchoScore` records persist as orphans. The next ETL run may create duplicate professors or fail uniqueness constraints.

**Warning signs:** `IntegrityError: duplicate key value violates unique constraint` during ETL re-runs.

**Prevention:** Add `cascade="all, delete-orphan"` to SQLAlchemy relationship definitions in `db/models.py`.

**Phase:** Bug-fix phase.

---

### Pitfall 15: Render Environment Variables Not Automatically Populated from `.env`

**What goes wrong:** Developers test locally with a `.env` file containing `DATABASE_URL`, `RMP_TOKEN`, etc. When deploying to Render, these values are not automatically transferred. The app starts with missing environment variables and fails with `KeyError` or connects to a nonexistent database.

**Warning signs:** Render logs show `KeyError: 'DATABASE_URL'` on first deploy.

**Prevention:** Before first deploy, manually add all required environment variables to Render's "Environment" panel. Maintain a `.env.example` file in the repo listing all required variables (with no values) so the checklist is explicit.

**Phase:** Deployment phase.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Bug fixes before FastAPI | Missing indexes not added (forgetting Alembic) | Add indexes in `create_all` or explicit migration before first deploy |
| FastAPI session setup | Using `scoped_session` instead of `Depends(get_db)` | Use `yield`-based dependency; `scoped_session` is deprecated for new code |
| FastAPI + APScheduler wiring | Scheduler jobs sharing request session | Each job creates its own `SessionLocal()` context |
| First API endpoint | Lazy-loaded relationships in Pydantic schema | Explicitly eager-load all serialized fields |
| pytest for API endpoints | TestClient bypassing SAVEPOINT fixture | Use `dependency_overrides` to inject fixture session |
| ETL E2E test | Real HTTP calls to RMP in CI | Mock HTTP layer for all scraper tests |
| Production deploy | DB expires in 30 days | Use Neon/Supabase or schedule pg_dump before day 30 |
| Production deploy | Vite bakes localhost URL into bundle | Set `VITE_API_URL` in Vercel dashboard, not .env |
| Public launch | Cold start with no user feedback | Add loading state + /health ping service |
| Public launch | Wildcard search DoS | Validate input length and character set at endpoint level |

---

## Sources

- [FastAPI + SQLAlchemy deadlock issue (GitHub Discussion #6628)](https://github.com/fastapi/fastapi/discussions/6628)
- [FastAPI + SQLAlchemy deadlock issue (GitHub Issue #3205)](https://github.com/fastapi/fastapi/issues/3205)
- [FastAPI APScheduler session management (GitHub Issue #4742)](https://github.com/fastapi/fastapi/issues/4742)
- [MissingGreenlet error: causes and solutions (greeden.me)](https://blog.greeden.me/en/2025/01/29/fastapi-causes-and-solutions-for-sqlalchemy-exc-missinggreenlet-error/)
- [Lazy loading of SQLAlchemy AsyncAttrs in response (GitHub Discussion #13125)](https://github.com/fastapi/fastapi/discussions/13125)
- [Render free PostgreSQL now expires after 30 days (Render Changelog)](https://render.com/changelog/free-postgresql-instances-now-expire-after-30-days-previously-90)
- [Render connection pooling documentation](https://render.com/docs/postgresql-connection-pooling)
- [Render free tier inactivity sleep (Render Community)](https://community.render.com/t/do-web-services-on-a-free-tier-go-to-sleep-after-some-time-inactive/3303)
- [CORS configuration in FastAPI (FastAPI official docs)](https://fastapi.tiangolo.com/tutorial/cors/)
- [CORS + cookies between FastAPI and React (sqlpey.com)](https://sqlpey.com/javascript/cors-cookie-fastapi-react-fix/)
- [Vite environment variables documentation](https://vite.dev/guide/env-and-mode)
- [FastAPI Dependencies with yield (official docs)](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/)
- [Session with FastAPI Dependency — SQLModel docs](https://sqlmodel.tiangolo.com/tutorial/fastapi/session-with-dependency/)
- [Async testing with FastAPI and pytest (weirdsheeplabs.com)](https://weirdsheeplabs.com/blog/fast-and-furious-async-testing-with-fastapi-and-pytest)

---

*Pitfalls audit: 2026-03-30*

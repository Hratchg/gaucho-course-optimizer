# External Integrations

**Analysis Date:** 2026-03-30

## External APIs & Data Sources

| Service | Purpose | Integration Method |
|---------|---------|-------------------|
| **RateMyProfessors** | Professor review scraping (ratings, comments, difficulty) | Internal GraphQL API endpoint: `https://www.ratemyprofessors.com/graphql` via `curl_cffi` |
| **Daily Nexus** | Grade distribution CSV data (Fall 2009–present) | GitHub raw file: `https://raw.githubusercontent.com/dailynexusdata/grades-data/main/courseGrades.csv` via Pandas |

## RateMyProfessors Integration

**GraphQL Endpoint:** `https://www.ratemyprofessors.com/graphql`

**Implementation:**
- Location: `scrapers/rmp_scraper.py`
- Client: `curl_cffi.requests` (Python library with TLS fingerprint mimicry)
- UCSB School ID: 1077 (hardcoded in queries)

**Queries Supported:**
1. **TeacherSearchPaginationQuery** (`TEACHER_SEARCH_QUERY`)
   - Fetches paginated teacher list (20 per page)
   - Retrieves: ID, name, department, ratings, difficulty, comments with dates
   - Pagination: `after` cursor-based pagination

2. **TeacherSearchQuery** (`NAME_SEARCH_QUERY`)
   - Targets specific professor by text name
   - Returns top 5 results with full details

**Authentication:** Not explicitly required (queries work without headers). RMP auth token stored in `.env` as `RMP_AUTH_TOKEN` (currently optional).

**Data Extracted:**
```python
{
  "legacy_id": int,
  "first_name": str,
  "last_name": str,
  "department": str,
  "avg_rating": float,
  "avg_difficulty": float,
  "would_take_again_pct": float,
  "num_ratings": int,
  "comments": [{
    "text": str,
    "date": str
  }]
}
```

**Related modules:**
- `scrapers/rmp_loader.py` — Loads parsed RMP data into database
- `scrapers/targeted_scrape.py` — Targeted scraping of active professors (min year: 2023)

## Daily Nexus Integration

**Data Source:** GitHub repository

**URL:** `https://raw.githubusercontent.com/dailynexusdata/grades-data/main/courseGrades.csv`

**Implementation:**
- Location: `scrapers/grades_ingester.py`
- Fetch method: Pandas `read_csv()` with GitHub raw file URL
- Loader: `scrapers/grades_loader.py` — Inserts records into database

**CSV Schema Mapping:**
| CSV Column | Internal Schema | Type | Purpose |
|-----------|-----------------|------|---------|
| course | course_code | string | E.g., "CMPSC 24" (normalized, spaces removed) |
| instructor | instructor | string | Professor name |
| quarter | quarter | string | E.g., "Fall", "Winter", "Spring", "Summer" |
| year | year | int | E.g., 2025 |
| Ap/A/Am/Bp/B/Bm/... | a_plus/a/a_minus/... | int | Grade count distribution |
| avgGPA | avg_gpa | float | Weighted average GPA for section |
| dept | department | string | Department code |

**Data Coverage:**
- Timespan: Fall 2009 through present (updated quarterly)
- Institution: UCSB only
- No authentication required (public GitHub repository)

## Databases

| Service | Purpose | Connection Method |
|---------|---------|-------------------|
| **PostgreSQL 16** | Core data store for courses, professors, grades, RMP reviews | Connection via SQLAlchemy: `DATABASE_URL` env var |

**Connection Details:**
- Location: `db/connection.py`
- Engine: SQLAlchemy 2.x with psycopg2-binary driver
- Pool Settings: `pool_pre_ping=True` (health checks on reuse)
- Session management: Sessionmaker-based session factory

**Models Location:** `db/models.py`
**Migrations Location:** `db/migrations/` (Alembic)

## File Storage

- **Type:** Local filesystem only
- **Data Directory:** `data/` (CSV downloads and temporary files)
- **No cloud storage integration** (S3, GCS, etc.)

## Caching & Session Storage

- **Streamlit Cache:** Built-in `@st.cache_data(ttl=3600)` for dashboard query results (1-hour TTL)
- **No Redis or Memcached integration**

## Authentication & Identity

- **RateMyProfessors:** Optional `RMP_AUTH_TOKEN` in `.env` (not required for scraping)
- **PostgreSQL:** Basic credentials in `docker-compose.yml` and `DATABASE_URL`
- **No third-party auth provider** (GitHub OAuth, Google Sign-in, etc.)

## Monitoring & Observability

**Logging:**
- Framework: Python `logging` module (standard library)
- Configuration: Basic setup via `logging.basicConfig(level=logging.INFO)` in `scheduler/jobs.py`
- No structured logging or third-party service integration detected

**Error Tracking:**
- Not detected (no Sentry, DataDog, etc.)

**Metrics/Analytics:**
- Not detected (no Prometheus, Google Analytics, etc.)

## CI/CD & Deployment

**CI Pipeline:**
- **Platform:** GitHub Actions
- **Workflow File:** `.github/workflows/test.yml`
- **Trigger:** Push to `master` branch or pull requests against `master`
- **Test Environment:** Ubuntu latest with PostgreSQL 16 service
- **Build Matrix:** Single job (Python 3.12)
- **Commands:**
  ```bash
  pip install -r requirements-dev.txt
  pytest -v
  ```

**Deployment:**
- **Target:** Docker + Docker Compose
- **Images:**
  - Dashboard: Builds from `Dockerfile` + runs `streamlit run dashboard/app.py --server.port=8501`
  - Scheduler: Builds from `Dockerfile` + runs `python -m scheduler.jobs`
  - Postgres: Pre-built `postgres:16` image
- **Orchestration:** Docker Compose (v3 format)
- **Container Registry:** Not configured (no DockerHub/ECR references)
- **Deployment Host:** Local development or self-hosted (not detected)

## Webhooks & Callbacks

**Incoming Webhooks:**
- Not detected (no webhook endpoints)

**Outgoing Webhooks:**
- Not detected (no third-party service callbacks)

## Background Jobs & Scheduling

**Scheduler Service:** APScheduler (BlockingScheduler)
- Location: `scheduler/jobs.py`
- Jobs:
  1. **RMP Targeted Refresh** (`rmp_targeted_refresh`)
     - Trigger: Every 2 days at 2:00 AM UTC (cron: `day="*/2", hour=2, minute=0`)
     - Steps: Scrape active professors (min year 2023) → Process NLP → Recompute scores

  2. **Quarterly Grade Update** (`quarterly_grade_update`)
     - Trigger: Monthly on 15th at 3:00 AM UTC (cron: `month="1,4,7,10", day=15, hour=3`)
     - Steps: Fetch Daily Nexus CSV → Load to database → Recompute scores

- Error Handling: Exceptions logged, jobs continue on next trigger

## Related External Data Sources

**Used within NLP & Scoring Pipelines:**
- **VADER Sentiment Dictionary** — Built-in to `vaderSentiment` library (no external fetch)
- **scikit-learn TF-IDF Model** — Fitted on-demand from stored comment text (no external model registry)

---

*Integration audit: 2026-03-30*

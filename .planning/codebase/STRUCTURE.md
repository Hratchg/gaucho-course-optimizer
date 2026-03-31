# Codebase Structure

**Analysis Date:** 2026-03-30

## Directory Layout

```
gaucho-course-optimizer/
├── db/                        # SQLAlchemy ORM and database connection
│   ├── __init__.py
│   ├── models.py              # SQLAlchemy declarative models (Professor, Course, GradeDistribution, etc.)
│   ├── connection.py          # Engine + session factory (global _engine, get_session())
│   └── migrations/            # Alembic version control
│       ├── env.py
│       └── versions/
│           └── 3ee0c9e2add3_initial_schema.py
├── scrapers/                  # Data ingestion from external sources
│   ├── __init__.py
│   ├── rmp_scraper.py         # RMP GraphQL client (RmpScraper class, search_teacher_by_name())
│   ├── rmp_loader.py          # Load RMP GraphQL data into DB (load_rmp_teacher_to_db())
│   ├── grades_ingester.py     # Fetch Daily Nexus grades CSV (fetch_grades_csv())
│   ├── grades_loader.py       # Parse and insert grade records (load_grades_to_db())
│   └── targeted_scrape.py     # Orchestrate RMP scrape by active professor (scrape_active_professors())
├── etl/                       # Data transformation and enrichment
│   ├── __init__.py
│   ├── name_matcher.py        # TheFuzz fuzzy matching utilities (normalize_nexus_name(), match_confidence())
│   ├── name_utils.py          # Name parsing helpers (parse_nexus_name(), find_duplicate_pairs())
│   ├── department_mapper.py   # UCSB dept code ↔ RMP dept name mapping (departments_match())
│   ├── enhanced_matcher.py    # 4-pass local professor matching (run_enhanced_matching())
│   ├── nlp_processor.py       # VADER sentiment + TF-IDF keywords (process_all_comments())
│   └── scoring.py             # Gaucho Value Score computation (compute_gaucho_score(), compute_all_scores())
├── dashboard/                 # Streamlit web application
│   ├── __init__.py
│   ├── app.py                 # Main Streamlit app (page layout, interactive widgets)
│   └── queries.py             # SQL query functions (search_courses(), get_professors_for_course())
├── scheduler/                 # APScheduler job definitions
│   ├── __init__.py
│   └── jobs.py                # Scheduled jobs (rmp_targeted_refresh(), quarterly_grade_update(), create_scheduler())
├── scripts/                   # CLI entry points
│   ├── run_pipeline.py        # Manual pipeline orchestration (full, --scrape, --match, --nlp, --score)
│   ├── export_db.sh           # Database dump to SQL file
│   └── import_db.sh           # Database restore from SQL file
├── tests/                     # pytest test suite
│   ├── conftest.py            # pytest fixtures (test DB session with rollback)
│   ├── fixtures/              # Test data (JSON responses)
│   │   ├── rmp_graphql_response.json
│   │   └── rmp_name_search_response.json
│   └── test_*.py              # 18 test modules (see list below)
├── docs/                      # Project documentation
│   ├── PRD.md
│   └── plans/
│       ├── 2026-02-25-gaucho-course-optimizer-design.md
│       ├── 2026-02-25-targeted-rmp-pipeline-implementation.md
│       ├── 2026-02-26-enhanced-matching-implementation.md
│       └── prod.md
├── data/                      # Static data / backups
│   └── gco_dump.sql           # Database dump (13 MB)
├── .github/                   # CI/CD configuration
├── docker-compose.yml         # PostgreSQL + Streamlit containers
├── Dockerfile                 # Application container
├── pyproject.toml             # Python project metadata + pytest config
├── requirements.txt           # Runtime dependencies
├── requirements-dev.txt       # Dev dependencies (pytest, etc.)
├── alembic.ini                # Database migration config
├── .env.example               # Environment variable template
└── README.md                  # Project overview

```

## Directory Purposes

**`db/`**
- Purpose: Database layer (ORM, migrations, session management)
- Contains: SQLAlchemy models, Alembic version control, connection factory
- Key files: `models.py` (7 tables: Professor, Course, GradeDistribution, RmpRating, RmpComment, GauchoScore), `connection.py` (global engine)

**`scrapers/`**
- Purpose: External data ingestion
- Contains: RMP GraphQL API client, Daily Nexus CSV parser, loaders
- Key files: `targeted_scrape.py` (main entry), `rmp_scraper.py` (API calls), `rmp_loader.py` (DB insert)

**`etl/`**
- Purpose: Data transformation (matching, NLP, scoring)
- Contains: Fuzzy matching, name normalization, sentiment analysis, score computation
- Key files: `enhanced_matcher.py` (4-pass linking), `nlp_processor.py` (VADER + TF-IDF), `scoring.py` (Gaucho Score formula)

**`dashboard/`**
- Purpose: User-facing web interface
- Contains: Streamlit app, query layer
- Key files: `app.py` (widgets, layout), `queries.py` (SQL helpers)

**`scheduler/`**
- Purpose: Batch job scheduling
- Contains: APScheduler definitions
- Key files: `jobs.py` (cron triggers, refresh logic)

**`scripts/`**
- Purpose: CLI entry points
- Contains: Pipeline orchestration, DB management
- Key files: `run_pipeline.py` (manual trigger)

**`tests/`**
- Purpose: pytest test coverage
- Contains: 18 test modules + fixtures
- Key files: `conftest.py` (DB session fixture with rollback)

**`docs/`**
- Purpose: Documentation
- Contains: PRD, design docs, deployment guides
- Key files: PRD.md, plans/

**`data/`**
- Purpose: Static backups / exports
- Contains: SQL dumps
- Key files: `gco_dump.sql` (13 MB)

## Key File Locations

| What | Where |
|------|-------|
| **Entry point (Dashboard)** | `dashboard/app.py` |
| **Entry point (Pipeline)** | `scripts/run_pipeline.py` |
| **Entry point (Scheduler)** | `scheduler/jobs.py` → `create_scheduler()` |
| **Database models** | `db/models.py` |
| **Database connection** | `db/connection.py` |
| **Config (environment)** | `.env` (from `.env.example`) |
| **Migrations** | `db/migrations/versions/` |
| **Core business logic** | `etl/enhanced_matcher.py`, `etl/nlp_processor.py`, `etl/scoring.py` |
| **RMP API integration** | `scrapers/rmp_scraper.py` |
| **Grade ingestion** | `scrapers/grades_ingester.py` |
| **Test database setup** | `tests/conftest.py` |
| **Test fixtures** | `tests/fixtures/` |

## Naming Conventions

**Files:**
- kebab-case for module names: `rmp_scraper.py`, `targeted_scrape.py`, `enhanced_matcher.py`
- UPPERCASE for config: `Dockerfile`, `README.md`, `.env.example`
- `test_*.py` for test modules: `test_nlp_processor.py`, `test_scoring.py`

**Classes:**
- PascalCase: `Professor`, `RmpScraper`, `BlockingScheduler`
- Database models match table names: `Professor` → `professors` table

**Functions:**
- snake_case: `scrape_active_professors()`, `get_professors_for_course()`, `compute_gaucho_score()`
- Prefix with verb: `get_*` (query), `fetch_*` (API), `load_*` (insert), `run_*` (execute), `process_*` (transform)

**Variables:**
- snake_case: `min_year`, `max_age_days`, `match_confidence`
- Prefix with underscore for internal: `_engine`, `_sia` (singleton instance)
- Plural for collections: `professors`, `results`, `keywords`

**Database:**
- Table names: plural snake_case: `grade_distributions`, `rmp_ratings`
- Column names: snake_case: `name_nexus`, `rmp_id`, `sentiment_score`
- Foreign keys: `[table]_id`: `professor_id`, `course_id`

## Where to Add New Code

**New Feature (e.g., add a new scoring factor):**
- Primary code: `etl/scoring.py` (add normalization function, update `compute_gaucho_score()`)
- Tests: `tests/test_scoring.py`
- Database schema: `db/models.py` (add column to `GauchoScore` if needed) + Alembic migration

**New ETL stage (e.g., regex cleaning):**
- Implementation: New file in `etl/` (e.g., `etl/text_cleaner.py`)
- Add to pipeline: `scripts/run_pipeline.py` (add `run_clean()` function and `--clean` arg)
- Tests: `tests/test_text_cleaner.py`
- Scheduled job: `scheduler/jobs.py` (add to `rmp_targeted_refresh()` or create new job)

**New Dashboard page:**
- Add to: `dashboard/app.py` (add new section or use Streamlit multi-page)
- Queries: `dashboard/queries.py` (add query function if needed)
- Tests: `tests/test_dashboard_queries.py`

**New External Integration (e.g., Slack notifications):**
- Client setup: `scrapers/` or new `integrations/` module
- Usage: `scheduler/jobs.py` (call from scheduled job)
- Tests: `tests/test_[integration].py`

**Database Schema Change:**
- Update model: `db/models.py` (add Column)
- Create migration: `alembic revision --autogenerate -m "add column X"`
- Run migration: `alembic upgrade head` (automatic in Docker)

**New CLI command:**
- Add to: `scripts/` (new file or extend `run_pipeline.py`)
- Import path: Must be at project root to use relative imports (see `sys.path.insert(0, ...)`)

## Special Directories

**`db/migrations/`**
- Purpose: Alembic version control for schema
- Generated: Yes (by `alembic revision`)
- Committed: Yes

**`tests/fixtures/`**
- Purpose: Mock API responses (JSON)
- Generated: No (manually created)
- Committed: Yes

**`data/`**
- Purpose: Database backups / static dumps
- Generated: Partially (exports/imports via shell script)
- Committed: SQL dump committed for quick restore

**`.github/`**
- Purpose: CI/CD workflows
- Generated: No (manually created)
- Committed: Yes

**`.planning/codebase/`**
- Purpose: GSD mapping documents (this file + others)
- Generated: Yes (by GSD mapper)
- Committed: Yes (generated output)

---

*Structure analysis: 2026-03-30*

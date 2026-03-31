# Technology Stack

**Analysis Date:** 2026-03-30

## Runtime & Language

- **Language:** Python 3.12+
- **Runtime:** CPython
- **Package Manager:** pip
- **Lockfile:** Not used (pinned in requirements.txt)

## Frameworks & Core Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| SQLAlchemy | >=2.0,<3 | ORM for database abstraction and queries |
| Alembic | >=1.13,<2 | Database schema migrations |
| psycopg2-binary | >=2.9,<3 | PostgreSQL database driver |
| Streamlit | >=1.41,<2 | Interactive web dashboard UI |
| Plotly | >=5.24,<6 | Interactive charts and visualizations |
| Pandas | >=2.2,<3 | Data manipulation and CSV parsing |
| curl_cffi | >=0.7 | HTTP client with TLS fingerprint mimicry for RMP scraping |
| thefuzz[speedup] | >=0.22 | Fuzzy string matching for professor name reconciliation |
| vaderSentiment | >=3.3 | Sentiment analysis of professor reviews |
| scikit-learn | >=1.6,<2 | Machine learning utilities (TF-IDF keyword extraction) |
| APScheduler | >=3.10,<4 | Job scheduling for background tasks |
| python-dotenv | >=1.0,<2 | Environment variable loading from `.env` files |

## Testing & Development

| Library | Version | Purpose |
|---------|---------|---------|
| pytest | >=8.3,<10 | Unit and integration test runner |
| pytest-mock | >=3.14,<4 | Mocking fixtures for tests |

## Configuration Files

- `pyproject.toml` — Project metadata and pytest configuration
- `requirements.txt` — Production dependencies with pinned versions
- `requirements-dev.txt` — Development dependencies (pytest, pytest-mock)
- `alembic.ini` — Alembic migration settings (script location: `db/migrations`)
- `.env.example` — Template for required environment variables
- `docker-compose.yml` — Container orchestration for PostgreSQL and application services
- `Dockerfile` — Container image build specification (Python 3.12-slim base)

## Build & Tooling

- **Build:** Docker (containerized via `Dockerfile`)
- **Database Migrations:** Alembic (configs at `db/migrations/`)
- **Linting:** Not detected (no eslint/flake8/ruff config found)
- **Formatting:** Not detected (no prettier/black config found)

## Database

- **Primary:** PostgreSQL 16 (specified in `docker-compose.yml`)
- **ORM:** SQLAlchemy 2.x
- **Connection Management:** Connection pooling via SQLAlchemy engine (`db/connection.py`)
- **Migrations Tool:** Alembic for schema versioning

## Environment & Configuration

**Required environment variables:**
- `DATABASE_URL` — PostgreSQL connection string (format: `postgresql://user:password@host:port/dbname`)
  - Development default: `postgresql://gco:gco@localhost:5432/gco`
  - Docker: `postgresql://gco:gco@db:5432/gco` (service-to-service)
- `RMP_AUTH_TOKEN` — Rate My Professors GraphQL authentication (optional, may be scraped without it)

**Configuration sources:**
- Environment variables via `os.environ.get()`
- `.env` file loaded by `python-dotenv` (see `scheduler/jobs.py`, `dashboard/app.py`)
- Docker Compose service environment (see `docker-compose.yml`)

## Containerization & Deployment

- **Base Image:** `python:3.12-slim`
- **Container Registry:** Not detected
- **Orchestration:** Docker Compose (3 services: postgres, dashboard, scheduler)
- **Dashboard Port:** 8501 (Streamlit default)
- **Database Port:** 5432 (PostgreSQL)

## Key Dependencies Rationale

**Critical for Core Operations:**
- **SQLAlchemy + psycopg2-binary** — Foundational for all data persistence and retrieval
- **curl_cffi** — Required for scraping RMP GraphQL API (TLS fingerprinting to avoid bot detection)
- **vaderSentiment** — Core NLP pipeline for comment sentiment scoring

**ETL & Data Processing:**
- **Pandas** — Grade CSV parsing and data transformation
- **thefuzz** — Professor name matching between RMP and Daily Nexus sources (essential for data integrity)
- **scikit-learn** — TF-IDF vectorization for keyword extraction from reviews

**Scheduling & Orchestration:**
- **APScheduler** — Triggers nightly RMP refreshes and quarterly grade updates on cron schedule

**UI & Visualization:**
- **Streamlit** — Rapid interactive dashboard development with caching
- **Plotly** — Rich, interactive grade distribution charts and trend visualizations

---

*Stack analysis: 2026-03-30*

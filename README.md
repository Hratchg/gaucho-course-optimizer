[![Tests](https://github.com/Hratchg/gaucho-course-optimizer/actions/workflows/test.yml/badge.svg)](https://github.com/Hratchg/gaucho-course-optimizer/actions/workflows/test.yml)

# Gaucho Course Optimizer

A production dashboard for UCSB students that correlates grade distributions with RateMyProfessors sentiment. Search by course, see professors ranked by a configurable "Gaucho Value Score."

## Features

- **Course search** with autocomplete — find any UCSB course
- **Professor ranking** by Gaucho Value Score (0-100, configurable weights)
- **Grade distributions** — bar charts, avg GPA, trends over time (Fall 2009-present)
- **RMP integration** — quality, difficulty, sentiment analysis, keyword tags
- **Recent comments** — 5 most recent student reviews with sentiment badges
- **Real-time re-ranking** via weight sliders (GPA, Quality, Difficulty, Sentiment)
- **Filters** — minimum year and department

## Screenshots

<!-- TODO: Add dashboard screenshots -->

## Prerequisites

- Python 3.12+
- Docker Desktop (for PostgreSQL)
- A populated PostgreSQL database (see Quick Start)

## Tech Stack

- **Dashboard:** Streamlit + Plotly
- **Database:** PostgreSQL 16
- **Scraping:** curl_cffi (RMP GraphQL), Pandas (Daily Nexus CSV)
- **NLP:** VADER sentiment + TF-IDF keyword extraction
- **Matching:** TheFuzz + multi-pass enhanced matcher (initial, fuzzy, dept disambiguation, dedup)
- **Scheduling:** GitHub Actions cron (nightly UCSB schedule sync, weekly RMP refresh, weekly Neon backup, quarterly Daily Nexus grades load); `scheduler/jobs.py` holds the job bodies
- **CI:** GitHub Actions
- **Deployment:** Docker Compose

## Quick Start

```bash
# Clone
git clone https://github.com/Hratchg/gaucho-course-optimizer.git
cd gaucho-course-optimizer

# Configure
cp .env.example .env
# Edit .env with your DATABASE_URL

# Launch
docker compose up

# Visit http://localhost:8501
```

## Pipeline

```bash
python scripts/run_pipeline.py              # full pipeline (scrape -> match -> NLP -> score)
python scripts/run_pipeline.py --scrape     # targeted RMP scrape only
python scripts/run_pipeline.py --match      # enhanced professor matching only
python scripts/run_pipeline.py --nlp        # NLP sentiment/keywords only
python scripts/run_pipeline.py --score      # Gaucho Score computation only
```

## Running Tests

```bash
# Install dev dependencies (includes pytest)
pip install -r requirements-dev.txt

# Start a throwaway PostgreSQL (any free local port works)
docker run -d --rm --name gco-ci-pg -e POSTGRES_USER=gco -e POSTGRES_PASSWORD=gco \
  -e POSTGRES_DB=gco_test -p 5445:5432 postgres:16

# Run the full test suite against it
DATABASE_URL=postgresql://gco:gco@localhost:5445/gco_test pytest -v
```

Tests use savepoint-based transactions that roll back after each test, but the session **creates every table at the start and drops every table at the end**, so only ever point them at a throwaway database:

- `DATABASE_URL` comes from the environment only; the tests do not read `.env`, which holds the app's own (production) database. Without it, they use `postgresql://gco:gco@localhost:5432/gco_test`, which is what CI provides.
- pytest refuses to start unless `DATABASE_URL`'s host is `localhost`, `127.0.0.1` or `::1`, and names the host it refused. Set `ALLOW_REMOTE_TEST_DB=1` to override that, only for a disposable remote database.

## Database Management

Export and import scripts are provided for backing up and restoring the database:

```bash
# Export the database to a SQL dump
bash scripts/export_db.sh

# Import a SQL dump into the database
bash scripts/import_db.sh
```

## Project Structure

```
├── scrapers/           # RMP GraphQL scraper + grade CSV ingester
├── etl/                # Name matching, enhanced matching, NLP, scoring
│   ├── name_matcher.py        # TheFuzz fuzzy name matching
│   ├── name_utils.py          # Nexus name parsing (initials, dedup)
│   ├── department_mapper.py   # UCSB dept code <-> RMP dept name mapping
│   ├── enhanced_matcher.py    # 4-pass local matching engine
│   ├── nlp_processor.py       # VADER sentiment + TF-IDF keywords
│   └── scoring.py             # Gaucho Value Score computation
├── db/                 # SQLAlchemy models + Alembic migrations
├── dashboard/          # Streamlit app
├── scheduler/          # Job bodies the GitHub Actions workflows call (APScheduler for local runs)
├── scripts/            # CLI pipeline runner + DB export/import
├── tests/              # pytest suite
├── docs/               # PRD, design docs, plans
├── docker-compose.yml
└── pyproject.toml
```

## Data Sources

- **Grades:** [Daily Nexus Grade Distributions](https://github.com/dailynexusdata/grades-data) — Fall 2009 through Fall 2025
- **Reviews:** RateMyProfessors via internal GraphQL API (UCSB school ID: 1077)

## Documentation

- [Product Requirements](docs/PRD.md)
- [Design Document](docs/plans/2026-02-25-gaucho-course-optimizer-design.md)
- [Targeted RMP Pipeline](docs/plans/2026-02-25-targeted-rmp-pipeline-implementation.md)
- [Enhanced Matching Pipeline](docs/plans/2026-02-26-enhanced-matching-implementation.md)
- [Production Deployment](docs/plans/prod.md)
- [Operations handoff, 2026-09-29](docs/handoff/2026-09-29-operations-handoff.md): current state, scheduled jobs and open items. Start here.
- Runbooks: [reconcile the production schema](docs/runbooks/reconcile-production-schema.md), [delete orphan professors](docs/runbooks/delete-orphan-professors.md)
- [RMP link audit, 2026-09-29](docs/audits/2026-09-29-rmp-link-audit.md)

## License

[MIT](LICENSE)

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
- **Scheduling:** APScheduler (nightly RMP, quarterly grades)
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

# Run the full test suite (requires PostgreSQL running on localhost:5432)
pytest -v
```

The test suite expects a PostgreSQL database at `postgresql://gco:gco@localhost:5432/gco_test`. Tests use savepoint-based transactions that roll back after each test, so no test data persists.

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
├── scheduler/          # APScheduler jobs (every-2-day + quarterly)
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

## License

[MIT](LICENSE)

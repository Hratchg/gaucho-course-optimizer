# Gaucho Course Optimizer

A production dashboard for UCSB students that correlates grade distributions with RateMyProfessors sentiment. Search by course, see professors ranked by a configurable "Gaucho Value Score."

## Features

- **Course search** with autocomplete — find any UCSB course
- **Professor ranking** by Gaucho Value Score (0–100, configurable weights)
- **Grade distributions** — bar charts, avg GPA, trends over time (Fall 2009–present)
- **RMP integration** — quality, difficulty, sentiment analysis, keyword tags
- **Real-time re-ranking** via weight sliders (GPA, Quality, Difficulty, Sentiment)

## Tech Stack

- **Dashboard:** Streamlit + Plotly
- **Database:** PostgreSQL 16
- **Scraping:** curl_cffi (RMP GraphQL), Pandas (Daily Nexus CSV)
- **NLP:** VADER sentiment + TF-IDF keyword extraction
- **Matching:** TheFuzz for professor name reconciliation
- **Scheduling:** APScheduler (nightly RMP, quarterly grades)
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

## Project Structure

```
├── scrapers/           # RMP GraphQL scraper + grade CSV ingester
├── etl/                # Name matching, NLP processing, scoring engine
├── db/                 # SQLAlchemy models + Alembic migrations
├── dashboard/          # Streamlit app
├── scheduler/          # APScheduler jobs (nightly + quarterly)
├── tests/              # pytest suite
├── docs/               # PRD, design docs, plans
├── docker-compose.yml
└── requirements.txt
```

## Data Sources

- **Grades:** [Daily Nexus Grade Distributions](https://github.com/dailynexusdata/grades-data) — Fall 2009 through Fall 2025
- **Reviews:** RateMyProfessors via internal GraphQL API (UCSB school ID: 1077)

## Documentation

- [Product Requirements](docs/PRD.md)
- [Design Document](docs/plans/2026-02-25-gaucho-course-optimizer-design.md)

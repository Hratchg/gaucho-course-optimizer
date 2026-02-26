# Gaucho Course Optimizer — Design Document

**Date:** 2026-02-25
**Status:** APPROVED
**Author:** Lead Architect

## Overview

A full-stack production dashboard for UCSB students that correlates GPA distributions (Daily Nexus) with RateMyProfessors sentiment. Students search by course and see professors ranked by a configurable "Gaucho Value Score."

## Architecture

**Approach:** Monolith script pipeline. Scrapers and ETL run on a schedule, Streamlit reads directly from Postgres. No API layer.

```
gaucho-course-optimizer/
├── scrapers/
│   ├── rmp_scraper.py          # GraphQL scraper (curl_cffi)
│   └── grades_ingester.py      # Fetch + parse courseGrades.csv
├── etl/
│   ├── name_matcher.py         # TheFuzz LAST,FIRST ↔ FIRST LAST
│   ├── nlp_processor.py        # VADER sentiment + TF-IDF keywords
│   └── scoring.py              # Gaucho Value Score (Bayesian, configurable)
├── db/
│   ├── models.py               # SQLAlchemy ORM
│   ├── migrations/             # Alembic
│   └── connection.py           # Engine/session factory
├── dashboard/
│   └── app.py                  # Streamlit app
├── scheduler/
│   └── jobs.py                 # APScheduler (nightly + quarterly)
├── tests/
├── docs/
│   ├── PRD.md
│   ├── README.md
│   └── plans/
├── requirements.txt
├── docker-compose.yml
├── .env.example
└── pyproject.toml
```

## Data Sources

### Grade Distributions
- **Source:** `github.com/dailynexusdata/grades-data` → `courseGrades.csv`
- **Scope:** Fall 2009 – Fall 2025, instructor-level grade counts per course per quarter
- **Ingestion:** Pandas, normalize course codes (strip spaces), compute avg_gpa per row
- **Schedule:** Quarterly (new data each term)

### RateMyProfessors
- **Method:** GraphQL endpoint (`ratemyprofessors.com/graphql`) via `curl_cffi` for TLS fingerprint mimicry
- **Filter:** UCSB school ID `1077`
- **Captures:** Overall quality, difficulty, would-take-again %, raw comment text
- **Rate limiting:** 3–7s randomized delay between requests
- **Fallback:** `RateMyProfessorAPI` Python package if GraphQL rotates
- **Schedule:** Nightly (2 AM)

## Data Model (Postgres)

### professors
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| name_nexus | TEXT | LAST, FIRST format from grades CSV |
| name_rmp | TEXT | FIRST LAST format from RMP |
| rmp_id | INTEGER | RMP's internal professor ID |
| department | TEXT | |
| match_confidence | FLOAT | TheFuzz score (0–100) |

### courses
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| code | TEXT | Normalized, e.g. PSTAT120A |
| title | TEXT | |
| department | TEXT | |

### grade_distributions
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| professor_id | FK → professors | |
| course_id | FK → courses | |
| quarter | TEXT | e.g. "Fall" |
| year | INTEGER | |
| a_plus ... f_count | INTEGER | Letter grade counts |
| avg_gpa | FLOAT | Computed from counts |

### rmp_ratings
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| professor_id | FK → professors | |
| overall_quality | FLOAT | 0–5 |
| difficulty | FLOAT | 0–5 |
| would_take_again_pct | FLOAT | |
| num_ratings | INTEGER | |
| fetched_at | TIMESTAMP | |

### rmp_comments
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| rmp_rating_id | FK → rmp_ratings | |
| comment_text | TEXT | |
| sentiment_score | FLOAT | VADER: -1 to +1 |
| keywords | JSONB | Extracted tags |
| created_at | TIMESTAMP | |

### gaucho_scores
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| professor_id | FK → professors | |
| course_id | FK → courses | |
| score | FLOAT | 0–100 |
| weights_used | JSONB | Which weights produced this score |
| computed_at | TIMESTAMP | |

## Name Matching

- Nexus: `LAST, FIRST` → split, normalize (lowercase, strip titles)
- RMP: `FIRST LAST` → split, normalize
- Algorithm: `TheFuzz.fuzz.token_sort_ratio`
- Thresholds: **85+** auto-link, **70–84** flag for review, **<70** no match
- Store `match_confidence` on `professors` table

## NLP Processing

- **Sentiment:** VADER (`nltk`) on each comment → score -1 to +1, aggregate mean per professor
- **Keywords:** TF-IDF (`scikit-learn`) across professor's comments → top 5–8 distinctive terms
- Map common phrases to readable tags ("tough grader", "clear lectures", etc.)

## Gaucho Value Score

Four signals, each normalized 0–1:
1. **GPA Factor** — Long-term avg GPA relative to department median
2. **Quality Factor** — RMP overall quality (0–5 → 0–1)
3. **Difficulty Factor** — Inverted RMP difficulty (lower = higher score)
4. **Sentiment Factor** — Aggregate comment sentiment

**Bayesian weighting:** Professors with <5 ratings pulled toward department mean.

**Configurable:** Dashboard exposes 4 sliders (default 0.25 each). Pre-computed with default weights in `gaucho_scores`; custom weights computed on-the-fly in Streamlit.

Final score: weighted sum → 0–100 scale.

## Dashboard (Streamlit)

### Flow
1. Homepage → course code search bar with autocomplete
2. Results: professors ranked by Gaucho Value Score

### Professor Card
- Header: name, score (color-coded green/yellow/red), match confidence badge
- Left: grade distribution bar chart, avg GPA, std deviation
- Right: RMP quality, difficulty, would-take-again %, sentiment gauge
- Tags: keyword chips ("clear lectures", "tough exams")
- Expandable: GPA trend line chart + recent comments

### Sidebar
- 4 weight sliders (re-rank in real time)
- Department filter
- Quarter range filter

### Tech
- `st.cache_data` (TTL: 1 hour)
- SQLAlchemy via `st.connection`
- Plotly for charts

## Scheduling & Ops

### APScheduler
- Persistent job store (Postgres-backed)
- Nightly (2 AM): RMP scrape → NLP → score recomputation
- Quarterly: grade ingestion → name matching → score recomputation
- `job_runs` table tracks status, errors, duration

### Docker Compose
```yaml
services:
  db:        # Postgres 16
  dashboard: # Streamlit (port 8501)
  scheduler: # APScheduler (long-running)
```

### Deployment
- VPS/cloud VM (Railway, Render, or DigitalOcean)
- `docker compose up` for all services
- `.env` for secrets (`DATABASE_URL`, RMP auth headers)
- Alembic migrations on startup

### Monitoring
- `job_runs` table for scraper health
- Dashboard data freshness badge
- Logging to stdout (Docker logs)

## Testing
- `pytest` with fixtures per pipeline stage
- Mock RMP GraphQL responses
- Snapshot tests for name matching (known professor pairs)
- Integration: CSV → DB → score → verify ranking

## Tech Stack Summary
- **Language:** Python 3.12+
- **Dashboard:** Streamlit
- **Database:** PostgreSQL 16
- **ORM:** SQLAlchemy + Alembic
- **Scraping:** curl_cffi (primary), RateMyProfessorAPI (fallback)
- **NLP:** VADER (nltk), TfidfVectorizer (scikit-learn)
- **Fuzzy Matching:** TheFuzz
- **Charts:** Plotly
- **Scheduling:** APScheduler
- **Containerization:** Docker Compose

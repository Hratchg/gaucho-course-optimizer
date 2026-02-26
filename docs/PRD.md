# Gaucho Course Optimizer — Product Requirements Document

**Version:** 1.0
**Date:** 2026-02-25
**Status:** Active

## Problem Statement

UCSB students choosing courses lack a unified view of professor quality. Grade distributions (Daily Nexus) and student reviews (RateMyProfessors) exist in separate silos. Students must manually cross-reference multiple sources to make informed decisions about which section to enroll in.

## Solution

A production Streamlit dashboard that merges UCSB grade distribution data with RateMyProfessors ratings and sentiment analysis. Students search by course code and see professors ranked by a configurable "Gaucho Value Score."

## Target User

UCSB undergraduate and graduate students selecting course sections during registration.

## Core Features

### F1: Course Search
- Autocomplete search bar for course codes (e.g., "PSTAT 120A")
- Returns all professors who have taught the course

### F2: Professor Ranking
- Professors ranked by Gaucho Value Score (0–100)
- Color-coded scores (green/yellow/red)
- Professor cards showing grade stats, RMP ratings, and sentiment tags

### F3: Configurable Scoring
- 4 weight sliders: GPA, Quality, Difficulty, Sentiment
- Real-time re-ranking as sliders adjust
- Default: equal weights (25% each)

### F4: Grade Distribution Visualization
- Bar charts of letter grade distribution per professor
- Long-term average GPA and standard deviation
- GPA trend over time (expandable line chart)

### F5: RMP Integration
- Overall quality, difficulty, would-take-again percentage
- Sentiment gauge from NLP analysis
- Keyword tags extracted from comments ("clear lectures", "tough exams")
- Recent comments viewable in expandable section

### F6: Filtering
- Department filter
- Quarter range filter (e.g., "2020 onwards")

## Data Sources

| Source | Format | Update Frequency |
|---|---|---|
| Daily Nexus grades-data (GitHub) | CSV | Quarterly |
| RateMyProfessors GraphQL API | JSON | Nightly |

## Non-Functional Requirements

- **Performance:** Dashboard loads search results in <2 seconds
- **Freshness:** RMP data no more than 24 hours stale; grades updated each quarter
- **Reliability:** Scraper failures logged and retried; dashboard stays up independently
- **Scalability:** Handles all UCSB courses and professors (~2000+ faculty)
- **Deployment:** Docker Compose on a cloud VM, single-command startup

## Tech Stack

- Python 3.12+, Streamlit, PostgreSQL 16, SQLAlchemy, Alembic
- curl_cffi, TheFuzz, VADER (nltk), scikit-learn, Plotly, APScheduler
- Docker Compose

## Success Metrics

- All UCSB professors with 5+ RMP ratings are matched and scored
- Name matching accuracy >90% (validated against manual sample)
- Dashboard search-to-results in <2 seconds
- Nightly scraper completes without failure for 7 consecutive days

## Out of Scope (v1)

- Professor-first search (search by professor name)
- Department-level overview pages
- Mobile-optimized layout
- User accounts or saved preferences
- LLM-generated professor summaries

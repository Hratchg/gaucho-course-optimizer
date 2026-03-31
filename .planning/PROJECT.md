# Gaucho Course Optimizer

## What This Is

A tool for UCSB students to find the best professor for any course using real grade distribution data (Daily Nexus) and Rate My Professors reviews. The backend pipeline scrapes, matches, and scores professor-course combinations into a 0–100 "Gaucho Score." The goal is to replace the existing Streamlit prototype with a polished React + FastAPI web app deployed publicly so students can actually use it.

## Core Value

Students can search any UCSB course and instantly see which professor will give them the best outcome — ranked by a score that combines GPA, RMP quality, difficulty, and sentiment.

## Requirements

### Validated

- ✓ ETL pipeline: Scrape → Match → NLP → Score — existing
- ✓ Gaucho Score computation (0–100 weighted, Bayesian-adjusted) — existing
- ✓ PostgreSQL database with SQLAlchemy ORM models — existing
- ✓ APScheduler jobs for automated data refresh (nightly RMP, quarterly grades) — existing
- ✓ Docker Compose dev environment — existing
- ✓ Streamlit dashboard (prototype: course search, professor rankings, weight sliders) — existing

### Active

- [ ] Pipeline verified end-to-end with real data (run scrape → match → score, confirm output)
- [ ] Critical bugs fixed: N+1 queries, no connection pooling, hardcoded credentials, missing DB indexes
- [ ] Automated pytest test suite covering pipeline, matching, scoring, and API endpoints
- [ ] FastAPI backend exposing course search and professor ranking endpoints
- [ ] React frontend: course search, professor cards, grade distribution charts, Gaucho Score display
- [ ] Deployed publicly — React on Vercel, FastAPI + PostgreSQL on Render (free tier)

### Out of Scope

- User accounts / saved searches — adds auth complexity, not needed for v1
- Real-time score updates — batch pipeline is sufficient
- Mobile app — responsive web is enough
- Replacing the scheduler — APScheduler stays as-is
- Admin dashboard — internal tooling out of scope for student-facing app

## Context

- **UCSB-specific:** "Gaucho" is the UCSB mascot; target users are UCSB undergrads planning their schedule
- **Data sources:** Daily Nexus grade CSVs (quarterly, fetched via scheduled job) + Rate My Professors GraphQL API
- **Existing code quality:** Pipeline logic is well-structured but has known bugs (N+1 queries in dashboard, no connection pooling, hardcoded RMP auth token, SQL injection risk in search). These must be fixed before building the public-facing API.
- **Test infrastructure:** pytest + pytest-mock already set up; some tests exist (`tests/test_enhanced_matcher.py`, `tests/test_name_utils.py`, `tests/test_dashboard_queries.py`) but no end-to-end coverage
- **Deployment target:** Free tier — Vercel (React), Render (FastAPI + PostgreSQL)

## Constraints

- **Tech Stack:** Python backend (FastAPI replaces Streamlit query layer), React frontend — keep existing ETL/scheduler/DB intact
- **Budget:** Free hosting only (Vercel + Render free tiers)
- **Database:** PostgreSQL — no migration to another DB
- **Data freshness:** RMP scraper must avoid rate limiting; existing 2–4s delay must be preserved

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Replace Streamlit with React + FastAPI | Streamlit can't be deployed as a proper public web app; React gives full UI control; FastAPI is natural fit for existing Python backend | — Pending |
| Keep existing ETL/scheduler intact | Pipeline is well-built; only the presentation layer needs replacing | — Pending |
| Fix bugs before building frontend | N+1 queries and missing indexes would make API unacceptably slow | — Pending |
| Free hosting (Vercel + Render) | Student project with no budget | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-30 after initialization*

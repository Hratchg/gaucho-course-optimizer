# Gaucho Course Optimizer

## Current Milestone: v1.1 UI/UX Overhaul

**Goal:** Transform the app from a functional MVP into a polished, branded experience with proper navigation, a tutorial landing page, and simplified weight controls.

**Target features:**
- Deep Teal + Amber branding (primary #0F766E, accent #D97706) with professional typography and cohesive visual identity
- Navigation system with navbar routing, breadcrumbs, and consistent back-navigation
- Tutorial landing page explaining Gaucho Score, factor meanings, calculation methodology, and guiding students to search
- Toggle-based weight controls replacing sliders with student-friendly checkboxes ("Easy Grades", "Great Teaching", "Low Difficulty", "Good Reviews") and auto-distributed weights
- Overall UI polish — clean flat design, responsive improvements, accessibility enhancements

## What This Is

A tool for UCSB students to find the best professor for any course using real grade distribution data (Daily Nexus) and Rate My Professors reviews. The backend pipeline scrapes, matches, and scores professor-course combinations into a 0–100 "Gaucho Score." The goal is to replace the existing Streamlit prototype with a polished React + FastAPI web app deployed publicly so students can actually use it.

## Core Value

Students can search any UCSB course and instantly see which professor will give them the best outcome — ranked by a score that combines GPA, RMP quality, difficulty, and sentiment.

## Requirements

### Validated

- ✓ ETL pipeline: Scrape → Match → NLP → Score — v1.0
- ✓ Gaucho Score computation (0–100 weighted, Bayesian-adjusted) — v1.0
- ✓ PostgreSQL database with SQLAlchemy ORM models — v1.0
- ✓ APScheduler jobs for automated data refresh (nightly RMP, quarterly grades) — v1.0
- ✓ Docker Compose dev environment — v1.0
- ✓ FastAPI backend (health, course search, professor ranking, grades, comments) — v1.0
- ✓ React frontend (course search, professor cards, grade charts, GPA trends, weight sliders) — v1.0
- ✓ Deployed publicly (Vercel frontend, Render backend, Neon PostgreSQL) — v1.0

### Active

- [ ] Deep Teal + Amber color scheme applied across all pages and components
- [ ] Professional typography system (heading + body font pairing)
- [ ] Navbar with routing across distinct pages (Home/Tutorial, Search, Course Results)
- [ ] Breadcrumb navigation for page orientation and back-navigation
- [ ] Tutorial landing page explaining Gaucho Score, factors, and calculation methodology
- [ ] Toggle-based weight controls replacing sliders with student-friendly labels and auto-distributed weights
- [ ] Responsive and accessibility improvements across all views

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
*Last updated: 2026-04-02 — Milestone v1.1 started*

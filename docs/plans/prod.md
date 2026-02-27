# Gaucho Course Optimizer — Production Document

**Last Updated:** 2026-02-26
**Status:** Pipeline complete. Enhanced matching code merged, awaiting production DB run.

---

## Table of Contents

1. [Architecture](#architecture)
2. [Tech Stack](#tech-stack)
3. [Data Model](#data-model)
4. [Implementation History](#implementation-history)
   - [Phase 1: Core Build (17 tasks)](#phase-1-core-build)
   - [Phase 2: Targeted RMP Pipeline (9 tasks)](#phase-2-targeted-rmp-pipeline)
   - [Phase 3: Enhanced Matching (5 tasks)](#phase-3-enhanced-matching)
5. [Pipeline Usage](#pipeline-usage)
6. [Project Structure](#project-structure)
7. [Key Algorithms](#key-algorithms)
8. [Known Issues & Gotchas](#known-issues--gotchas)
9. [Resume Point](#resume-point)
10. [Future Work](#future-work)

---

## Architecture

Monolith script pipeline. Scrapers and ETL run on a schedule (APScheduler). Streamlit reads directly from Postgres via SQLAlchemy. No API layer. Docker Compose orchestrates Postgres, dashboard, and scheduler as three services.

```
Daily Nexus CSV ──→ grades_ingester ──→ grades_loader ──→ PostgreSQL
                                                              │
RMP GraphQL ──→ rmp_scraper ──→ targeted_scrape ──→ rmp_loader ──→│
                                                              │
                                    enhanced_matcher ─────────→│
                                                              │
                              nlp_processor (VADER + TF-IDF) ←─┤
                              scoring (Gaucho Value Score)   ←─┤
                                                              │
                              Streamlit dashboard ←────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.12+ |
| Dashboard | Streamlit + Plotly |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy + Alembic |
| RMP Scraping | curl_cffi (TLS fingerprint mimicry) |
| Fuzzy Matching | TheFuzz (token_sort_ratio) |
| Enhanced Matching | 4-pass local engine (name_utils, dept_mapper) |
| NLP | VADER (nltk), TfidfVectorizer (scikit-learn) |
| Scheduling | APScheduler (every-2-day + quarterly) |
| Containerization | Docker Compose |

## Data Model

### professors
| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| name_nexus | TEXT | "LAST, FIRST" or "LAST F" from grades CSV |
| name_rmp | TEXT | "First Last" from RMP |
| rmp_id | INTEGER UNIQUE | RMP's internal professor ID |
| department | TEXT | |
| match_confidence | FLOAT | Match score (0-100) |

### courses
| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| code | TEXT UNIQUE | Normalized, e.g. PSTAT120A |
| title | TEXT | |
| department | TEXT | |

### grade_distributions
| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| professor_id | FK -> professors | NOT NULL |
| course_id | FK -> courses | NOT NULL |
| quarter | TEXT | e.g. "Fall" |
| year | INTEGER | |
| a_plus ... f | INTEGER | Letter grade counts |
| avg_gpa | FLOAT | Computed from counts |

### rmp_ratings
| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| professor_id | FK -> professors | NOT NULL |
| overall_quality | FLOAT | 0-5 |
| difficulty | FLOAT | 0-5 |
| would_take_again_pct | FLOAT | |
| num_ratings | INTEGER | |
| fetched_at | TIMESTAMP | |

### rmp_comments
| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| rmp_rating_id | FK -> rmp_ratings | NOT NULL |
| comment_text | TEXT | |
| sentiment_score | FLOAT | VADER: -1 to +1 |
| keywords | JSONB | Extracted tags |
| created_at | TIMESTAMP | |

### gaucho_scores
| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| professor_id | FK -> professors | NOT NULL |
| course_id | FK -> courses | NOT NULL |
| score | FLOAT | 0-100 |
| weights_used | JSONB | Weight configuration used |
| computed_at | TIMESTAMP | |

---

## Implementation History

### Phase 1: Core Build

**Date:** 2026-02-25
**Status:** COMPLETE — 17 tasks, 31 tests, all passing
**Design doc:** `2026-02-25-gaucho-course-optimizer-design.md`
**Implementation plan:** `2026-02-25-gaucho-course-optimizer-implementation.md`

| Task | Component | Tests | Status |
|------|-----------|-------|--------|
| 1 | Project scaffolding (`pyproject.toml`, `requirements.txt`, `.env.example`, `.gitignore`, `conftest.py`) | conftest.py | DONE |
| 2 | DB connection (`db/connection.py`) | 2 | DONE |
| 3 | ORM models (`db/models.py` — 6 tables) | 3 | DONE |
| 4 | Alembic migrations (`db/migrations/`) | — | DONE |
| 5 | Docker Compose — Postgres 16 | — | DONE |
| 6 | Grade CSV parser (`scrapers/grades_ingester.py`) | 3 | DONE |
| 7 | Grade DB loader (`scrapers/grades_loader.py`) | 2 | DONE |
| 8 | RMP GraphQL scraper (`scrapers/rmp_scraper.py`) | 2 | DONE |
| 9 | RMP DB loader (`scrapers/rmp_loader.py`) | 1 | DONE |
| 10 | Name matching — TheFuzz (`etl/name_matcher.py`) | 6 | DONE |
| 11 | NLP processor — VADER + TF-IDF (`etl/nlp_processor.py`) | 4 | DONE |
| 12 | Scoring engine (`etl/scoring.py`) | 6 | DONE |
| 13 | Streamlit dashboard (`dashboard/app.py`, `dashboard/queries.py`) | manual | DONE |
| 14 | APScheduler (`scheduler/jobs.py`) | 1 | DONE |
| 15 | Docker Compose — full stack (Dockerfile, 3 services) | manual | DONE |
| 16 | Integration test (`tests/test_integration.py`) | 1 | DONE |
| 17 | README + docs update | — | DONE |

**Data loaded:**
- 5,976 professors from Daily Nexus grade CSV (Fall 2009 - Fall 2025)
- 103K+ grade distribution records
- 1,367 UCSB professors scraped from RMP (bulk scrape)

---

### Phase 2: Targeted RMP Pipeline

**Date:** 2026-02-25
**Status:** COMPLETE — 9 tasks, 14 tests, all passing
**Design doc:** `2026-02-25-targeted-rmp-pipeline-design.md`
**Implementation plan:** `2026-02-25-targeted-rmp-pipeline-implementation.md`

**Problem:** The bulk RMP scraper pages through ALL UCSB teachers — slow and fetches data we don't need. Need a smarter, targeted approach for active professors only.

**Solution:** For each active professor (taught 2023-2025), search RMP by name + UCSB school filter. Fuzzy match during scraping. Only save matches. Each professor committed individually for resumability.

| Task | Component | Tests | Status |
|------|-----------|-------|--------|
| 1 | Targeted name search (`scrapers/rmp_scraper.py` — `NAME_SEARCH_QUERY`, `search_teacher_by_name()`) | 1 | DONE |
| 2 | Active professor query (`scrapers/rmp_loader.py` — `get_active_professors()`, `is_stale()`) | 3 | DONE |
| 3 | Nexus professor linking (`scrapers/rmp_loader.py` — `nexus_professor_id` param) | 1 | DONE |
| 4 | Targeted scrape loop (`scrapers/targeted_scrape.py`) | 3 | DONE |
| 5 | Batch NLP processor (`etl/nlp_processor.py` — `process_all_comments()`) | 2 | DONE |
| 6 | Batch scoring engine (`etl/scoring.py` — `compute_all_scores()`) | 2 | DONE |
| 7 | Pipeline CLI script (`scripts/run_pipeline.py`) | — | DONE |
| 8 | Scheduler update (every-2-day cron) | 2 | DONE |
| 9 | Run full pipeline (manual execution) | — | DONE |

**Results of initial targeted scrape run:**
- 2,292 active professors searched
- 973 matched to RMP records (match confidence >= 85)
- ~1,300 had no RMP profile
- 19 collision errors (same-name professors at UCSB)
- Scraped comments, sentiment, and keywords populated

**Key design decisions:**
- Active professors only: 2023-2025 (2,292 of 5,976)
- Rate limiting: 2-4s random delay between RMP requests
- Staleness check: skip professors with `fetched_at` < 2 days old
- Fuzzy matching: `token_sort_ratio >= 85` auto-link, `70-84` review, `<70` skip
- Schedule: every 2 days at 2am (not nightly)

---

### Phase 3: Enhanced Matching

**Date:** 2026-02-26
**Status:** COMPLETE — code merged, 30 new tests passing, NOT yet run against production DB
**Implementation doc:** `2026-02-26-enhanced-matching-implementation.md`

**Problem:** The targeted scrape (Phase 2) fails for 86% of Nexus names because they are initial-only ("HUANG L"). Searching "L Huang" on RMP returns wrong/ambiguous results. Result: 19 collision errors, 0 new matches in 297 attempts.

**Root cause:** The 1,367 UCSB RMP professors are already in the DB. The problem is purely local matching — we need to match initial-only Nexus names against existing RMP records using last name + initial + department, not by re-searching the API.

**Solution:** A 4-pass local matching engine in `etl/enhanced_matcher.py` — no API calls.

| Pass | Strategy | Expected Matches |
|------|----------|-----------------|
| 1 | Initial match — last name + first initial, unique candidate only (conf 90/75) | ~379 |
| 2 | Full-name fuzzy — TheFuzz token_sort_ratio >= 85, dept boost +5 | ~50-100 |
| 3 | Department disambiguation — multiple candidates -> dept filter to 1 | ~10 |
| 4 | Nexus deduplication — merge "CHANG S" + "CHANG SHIYU" in same dept | ~9 merges |

**Expected improvement:** ~400-500 new matches (973 -> ~1,370-1,470), a ~40% increase.

| Task | Component | Tests | Status |
|------|-----------|-------|--------|
| 1 | Name parsing utilities (`etl/name_utils.py`) | 14 | DONE |
| 2 | Department mapper (`etl/department_mapper.py`) | 8 | DONE |
| 3 | 4-pass matching engine (`etl/enhanced_matcher.py`) | 8 | DONE |
| 4 | Wire into pipeline (`scripts/run_pipeline.py` — `--match` flag) | — | DONE |
| 5 | Run pipeline + re-export DB | — | PENDING |

**Files created:**

| File | Purpose |
|------|---------|
| `etl/name_utils.py` | `parse_nexus_name()`, `is_initial_only()`, `initial_matches()`, `find_duplicate_pairs()` |
| `etl/department_mapper.py` | `DEPT_MAP` (65 UCSB dept codes -> RMP names), `departments_match()` with fuzzy fallback |
| `etl/enhanced_matcher.py` | 4-pass engine: `run_enhanced_matching()` orchestrating all passes |
| `tests/test_name_utils.py` | 14 tests — parsing, initial detection, duplicate finding |
| `tests/test_department_mapper.py` | 8 tests — exact, case-insensitive, fuzzy, multi-name depts |
| `tests/test_enhanced_matcher.py` | 8 tests — DB-backed via SAVEPOINT fixture |

**Key implementation detail — SQLAlchemy cascade handling:**

When linking a Nexus professor to an RMP-only professor, the RMP row must be deleted. SQLAlchemy's default cascade behavior tries to null-ify FKs on related `rmp_ratings` rows, but `professor_id` is NOT NULL. Solution:
1. Transfer ratings to the Nexus professor
2. Clear `rmp_id` on the RMP row (avoid unique constraint violation)
3. Flush + `session.expire(rmp_prof)` to prevent cascade-nullify
4. Delete the RMP row
5. Set `rmp_id` on the Nexus professor

Same pattern in Pass 4 (deduplication).

---

## Pipeline Usage

```bash
python scripts/run_pipeline.py              # full: scrape -> match -> NLP -> score
python scripts/run_pipeline.py --scrape     # targeted RMP scrape only
python scripts/run_pipeline.py --match      # enhanced 4-pass matching only
python scripts/run_pipeline.py --nlp        # VADER sentiment + TF-IDF keywords
python scripts/run_pipeline.py --score      # Gaucho Value Score computation
```

**Pipeline order:** scrape -> match -> NLP -> score

**Scheduling:**
- Every 2 days at 2am: targeted RMP scrape -> NLP -> scoring
- Quarterly (Jan/Apr/Jul/Oct 15th at 3am): grade CSV ingestion -> matching -> scoring
- On-demand: `python scripts/run_pipeline.py`

---

## Project Structure

```
gaucho-course-optimizer/
├── scrapers/
│   ├── rmp_scraper.py          # GraphQL scraper (curl_cffi) + name search
│   ├── rmp_loader.py           # RMP data -> DB, active professor query
│   ├── grades_ingester.py      # Fetch + parse courseGrades.csv
│   ├── grades_loader.py        # Grade data -> DB (idempotent)
│   └── targeted_scrape.py      # Targeted scrape loop with fuzzy match
├── etl/
│   ├── name_matcher.py         # TheFuzz LAST,FIRST <-> FIRST LAST
│   ├── name_utils.py           # Nexus name parsing (initials, dedup)
│   ├── department_mapper.py    # UCSB dept code <-> RMP dept name (65 mappings)
│   ├── enhanced_matcher.py     # 4-pass local matching engine
│   ├── nlp_processor.py        # VADER sentiment + TF-IDF keywords
│   └── scoring.py              # Gaucho Value Score (Bayesian, configurable)
├── db/
│   ├── models.py               # SQLAlchemy ORM (6 tables)
│   ├── connection.py           # Engine/session factory
│   └── migrations/             # Alembic
├── dashboard/
│   ├── app.py                  # Streamlit app
│   └── queries.py              # DB query helpers
├── scheduler/
│   └── jobs.py                 # APScheduler (every-2-day + quarterly)
├── scripts/
│   └── run_pipeline.py         # CLI pipeline runner
├── tests/                      # 75 tests (pytest)
│   ├── conftest.py             # SAVEPOINT-based session fixture
│   ├── test_db_connection.py
│   ├── test_models.py
│   ├── test_grades_ingester.py
│   ├── test_grades_loader.py
│   ├── test_rmp_scraper.py
│   ├── test_rmp_loader.py
│   ├── test_name_matcher.py
│   ├── test_nlp_processor.py
│   ├── test_scoring.py
│   ├── test_scheduler.py
│   ├── test_integration.py
│   ├── test_active_professors.py
│   ├── test_targeted_scrape.py
│   ├── test_batch_nlp.py
│   ├── test_batch_scoring.py
│   ├── test_name_utils.py
│   ├── test_department_mapper.py
│   └── test_enhanced_matcher.py
├── docs/
│   ├── PRD.md
│   └── plans/
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## Key Algorithms

### Name Matching (TheFuzz)
- Nexus format: `LAST, FIRST` or `LAST F` (initial-only)
- RMP format: `First Last`
- Algorithm: `TheFuzz.fuzz.token_sort_ratio`
- Thresholds: **85+** auto-link, **70-84** flag for review, **<70** no match

### Enhanced Matching (4-Pass Local Engine)
- **Pass 1:** Initial-only names -> RMP by last name + first initial (unique candidate only)
- **Pass 2:** Full-name fuzzy against unlinked RMP records (threshold 85+)
- **Pass 3:** Ambiguous initials -> department disambiguation
- **Pass 4:** Nexus deduplication ("CHANG S" + "CHANG SHIYU" -> merge)

### Department Mapping
- 65-entry static map (Nexus codes -> RMP names)
- Multi-mapping supported (CHEM -> "Chemistry" OR "Chemistry And Biochemistry")
- Fuzzy fallback (threshold 80) for departments not in static map

### Gaucho Value Score
Four signals, each normalized 0-1:
1. **GPA Factor** — Long-term avg GPA relative to department median
2. **Quality Factor** — RMP overall quality (0-5 -> 0-1)
3. **Difficulty Factor** — Inverted RMP difficulty (lower = higher score)
4. **Sentiment Factor** — Aggregate comment sentiment (-1 to +1 -> 0 to 1)

**Bayesian weighting:** Professors with <5 ratings pulled toward department mean.
**Configurable:** Dashboard exposes 4 sliders (default 0.25 each). Custom weights computed on-the-fly in Streamlit.

### NLP Processing
- **Sentiment:** VADER (nltk) on each comment -> compound score -1 to +1
- **Keywords:** TF-IDF (scikit-learn) across professor's comments -> top 5-8 distinctive terms

---

## Known Issues & Gotchas

### SQLAlchemy Cascade on NOT NULL FKs
When deleting a professor row that has related `rmp_ratings` or `grade_distributions`, SQLAlchemy tries to SET NULL on the FK columns. But `professor_id` is NOT NULL, causing `IntegrityError`. **Fix:** Always call `session.expire(prof)` before `session.delete(prof)` to prevent cascade-nullify on already-transferred relationships.

### Unique Constraint on `rmp_id`
When linking a Nexus professor to an RMP professor, you must clear `rmp_id` on the source row and flush before setting it on the target row. Otherwise both rows momentarily have the same `rmp_id`, violating the unique constraint.

### Initial-Only Names (86% of Nexus)
Most Daily Nexus grade records use initial-only names ("HUANG L", "CHANG S"). These cannot be API-searched on RMP effectively. The enhanced matcher (Phase 3) handles this locally.

### curl_cffi TLS Fingerprint
RMP blocks standard `requests` library calls. `curl_cffi` with `impersonate="chrome"` mimics a real browser's TLS fingerprint.

### Rate Limiting
RMP requests use 2-4s random delays. Initial scrape of 2,292 professors takes ~60-120 minutes.

---

## Resume Point

To continue development on the laptop:

```bash
# 1. Pull latest code
cd /c/Users/King\ Hratch/gaucho-course-optimizer
git pull

# 2. Start Docker Desktop, then start DB
docker compose up db -d

# 3. Run enhanced matching against production data
python scripts/run_pipeline.py --match
# Watch logs — Pass 1-4 stats will print. Expected: ~400+ new matches.

# 4. Recompute NLP + scores with new matches
python scripts/run_pipeline.py --nlp --score

# 5. Verify match count
docker compose exec db psql -U gco -c \
  "SELECT count(*) FROM professors WHERE rmp_id IS NOT NULL AND name_nexus IS NOT NULL;"
# Should be ~1,370+ (up from 973)

# 6. Re-export DB
bash scripts/export_db.sh

# 7. Commit results
git add -A && git commit -m "data: run enhanced matching pipeline"
```

---

## Future Work

- [ ] Run enhanced matching against production DB (Phase 3, Task 5)
- [ ] Add image uploads for professor photos
- [ ] Email notifications for score changes
- [ ] Pagination in dashboard results
- [ ] Deploy to cloud (Railway / Render / DigitalOcean)
- [ ] Add more RMP data fields (tags, thumbs up/down)
- [ ] Historical score tracking (score trends over time)
- [ ] Mobile-responsive dashboard layout

---

## Test Summary

**75 tests total, 0 failures**

| Test File | Count | Phase |
|-----------|-------|-------|
| test_db_connection.py | 2 | 1 |
| test_models.py | 3 | 1 |
| test_grades_ingester.py | 3 | 1 |
| test_grades_loader.py | 2 | 1 |
| test_rmp_scraper.py | 3 | 1+2 |
| test_rmp_loader.py | 2 | 1+2 |
| test_name_matcher.py | 6 | 1 |
| test_nlp_processor.py | 4 | 1 |
| test_scoring.py | 6 | 1 |
| test_scheduler.py | 2 | 1+2 |
| test_integration.py | 1 | 1 |
| test_active_professors.py | 3 | 2 |
| test_targeted_scrape.py | 3 | 2 |
| test_batch_nlp.py | 2 | 2 |
| test_batch_scoring.py | 2 | 2 |
| test_name_utils.py | 14 | 3 |
| test_department_mapper.py | 8 | 3 |
| test_enhanced_matcher.py | 8 | 3 |

---

## Data Sources

- **Grades:** [Daily Nexus Grade Distributions](https://github.com/dailynexusdata/grades-data) — Fall 2009 through Fall 2025
- **Reviews:** RateMyProfessors via internal GraphQL API (UCSB school ID: 1077)

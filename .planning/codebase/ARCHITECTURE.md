# Architecture

**Analysis Date:** 2026-03-30

## Pattern Overview

**Overall:** Layered + Pipeline-Driven (ETL + Presentation)

**Key Characteristics:**
- Data ingestion pipeline with multiple specialized stages (Scrape → Match → NLP → Score)
- Separation of concerns: Data layer (DB), Business logic (ETL), Presentation (Dashboard)
- Scheduled batch processing for data refresh and NLP enrichment
- CLI entry point for manual pipeline execution with modular stages

## Layers

| Layer | Location | Responsibility |
|-------|----------|----------------|
| **Data Access** | `db/` | SQLAlchemy ORM models, database connection pooling, migrations (Alembic) |
| **Scraping** | `scrapers/` | External data ingestion (RMP GraphQL API, Daily Nexus CSV) |
| **ETL Processing** | `etl/` | Name matching, professor linking, NLP sentiment/keyword extraction, Gaucho Score computation |
| **Scheduling** | `scheduler/` | APScheduler jobs for nightly RMP refresh and quarterly grade updates |
| **Presentation** | `dashboard/` | Streamlit web UI with query layer for filtering/ranking professors |
| **CLI** | `scripts/` | Pipeline orchestration and manual trigger entry points |

## Data Flow

**Full Pipeline (Manual or Scheduled):**

1. **Scrape Phase** (`scrapers/targeted_scrape.py`)
   - Get unmatched Nexus professors (from `GradeDistribution` records)
   - Search RMP API for each professor by normalized name
   - Fuzzy match results, store RMP data if confidence >= 70%
   - Rate limit between requests (2–4s random delay)

2. **Matching Phase** (`etl/enhanced_matcher.py`)
   - 4-pass local matching engine (no API calls)
   - Runs only on unmatched Nexus professors and RMP-only records
   - Pass 1: Exact name match after normalization
   - Pass 2: Fuzzy match (TheFuzz) with threshold
   - Pass 3: Department + name match disambiguation
   - Pass 4: De-duplication by detecting professor name variants
   - Links Nexus professor to RMP record via `rmp_id` field

3. **NLP Phase** (`etl/nlp_processor.py`)
   - Batch process all unscored RMP comments
   - Sentiment analysis: VADER compound score (-1 to +1) per comment
   - Keyword extraction: TF-IDF vectorizer extracts top 8 distinctive keywords per professor
   - Store sentiment in `sentiment_score`, keywords in JSON `keywords` field

4. **Scoring Phase** (`etl/scoring.py`)
   - Compute Gaucho Value Score (0–100) for each professor-course pair
   - Normalize: GPA (0–1), Quality (0–1), Difficulty (inverted 0–1), Sentiment (-1 to +1 → 0–1)
   - Apply Bayesian adjustment to pull low-sample-size ratings toward prior
   - Final score = weighted sum of normalized factors × 100
   - Store in `GauchoScore` table with weights used

**Dashboard Request Flow:**

1. User searches course → `search_courses()` queries `Course` table
2. User selects course → `get_professors_for_course()` joins `GradeDistribution` + `Professor` + `RmpRating` + `RmpComment`
3. Dashboard calculates Gaucho Scores in real-time using user-selected weights
4. User adjusts weight sliders → scores recompute instantly (cached for 1 hour)

**Scheduled Jobs:**

- **Every 2 days @ 2 AM:** Scrape active RMP professors → NLP process comments → recompute scores
- **Quarterly @ 3 AM (1st month, 15th):** Fetch grades CSV from Daily Nexus → load into DB → recompute scores

## Key Abstractions

**Professor-Course Matching:**
- **Concept:** Match professors from two sources (Daily Nexus grades, RMP reviews)
- **Files:** `etl/name_matcher.py`, `etl/enhanced_matcher.py`, `etl/name_utils.py`
- **Pattern:** TheFuzz fuzzy matching with normalization; 4-pass local matching engine avoids API calls
- **Why:** Grades data has professor names from Nexus; reviews from RMP. Must link them to correlate data.

**Gaucho Value Score:**
- **Concept:** Single 0–100 score combining GPA, RMP quality, RMP difficulty, sentiment
- **Files:** `etl/scoring.py`
- **Pattern:** Normalize each dimension, apply Bayesian adjustment for small sample sizes, weighted sum
- **Why:** Enable real-time re-ranking via dashboard weight sliders; configure score formula without recompute

**RMP Data Freshness:**
- **Concept:** Avoid redundant API scrapes by tracking fetch timestamps
- **Files:** `scrapers/targeted_scrape.py`, `scrapers/rmp_loader.py`
- **Pattern:** Check `RmpRating.fetched_at` before scrape; skip if < 2 days old (configurable)
- **Why:** RMP API rate limiting; avoid unnecessary requests for unchanged data

**NLP Comment Processing:**
- **Concept:** Sentiment + keyword extraction for professor reviews
- **Files:** `etl/nlp_processor.py`
- **Pattern:** VADER for sentiment (built-in lexicon), TF-IDF for keywords (per-professor aggregation)
- **Why:** Enable "recent comments" with sentiment badges; "common keywords" for professor discovery

## Entry Points

**Manual Pipeline Execution:**
- Location: `scripts/run_pipeline.py`
- Triggers: User runs `python scripts/run_pipeline.py [--scrape|--match|--nlp|--score]`
- Responsibilities:
  - Create DB session
  - Call stage functions in order (or selected stage)
  - Log progress and stats (searched, matched, skipped, errors)
  - Close session on completion

**Scheduled Jobs:**
- Location: `scheduler/jobs.py`
- Triggers: APScheduler cron jobs (every 2 days, quarterly)
- Responsibilities:
  - RMP refresh job: Scrape → NLP → Recompute scores
  - Grade update job: Fetch CSV → Load → Recompute scores

**Dashboard:**
- Location: `dashboard/app.py`
- Triggers: User visits `http://localhost:8501` (Streamlit default)
- Responsibilities:
  - Search courses (text input with filter)
  - Display professors ranked by Gaucho Score
  - Show grade history (bar charts, GPA trend)
  - Display RMP data (quality, difficulty, recent comments with sentiment)
  - Enable real-time re-ranking via weight sliders

## Error Handling

**Strategy:** Try-catch with logging; rollback on DB errors; continue processing remaining records

**Patterns:**

- **Scraping errors:** Log error, skip professor, increment `errors` stat; catch per-request
- **Database errors:** Session rollback on `load_rmp_teacher_to_db()` failure; continue loop
- **NLP errors:** Treat empty comments as 0.0 sentiment; skip keywords if < 2 comments per professor
- **Pipeline interruption:** Catch `KeyboardInterrupt` in main loop; log "partial progress is saved"

## Cross-Cutting Concerns

**Logging:**
- Framework: Python `logging` module
- Approach: Structured logs with timestamps, level (INFO/ERROR), and message
- Pattern: Per-module loggers (e.g., `logger = logging.getLogger(__name__)`)
- Info level logs for pipeline progress (scraped N professors, matched M, etc.)
- Error level for exceptions (API timeouts, DB insert failures)

**Validation:**
- Confidence thresholds (fuzzy match >= 70%, auto-match >= 85%)
- Data freshness checks (skip RMP if fetched < max_age_days)
- Empty/None checks (skip unmatched professors, skip empty comments for keywords)
- Type coercion (convert avg_gpa to float, clamp scores 0–100)

**Database Transactions:**
- Per-stage session: Each job/pipeline run gets its own session
- Savepoint-based rollback for tests (see `conftest.py`)
- Commit at end of each major phase (NLP, Scoring)
- Session close in finally block for cleanup

**Rate Limiting:**
- RMP scraper: Random 2–4s delay between searches
- No delay for re-runs (check `fetched_at` first)
- Purpose: Avoid RMP API throttling

---

*Architecture analysis: 2026-03-30*

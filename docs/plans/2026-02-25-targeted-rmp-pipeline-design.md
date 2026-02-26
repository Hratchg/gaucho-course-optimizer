# Targeted RMP Pipeline Design

**Date:** 2026-02-25
**Status:** APPROVED

## Problem

The Gaucho Course Optimizer has 5,976 professors and 103K grade distributions loaded from Daily Nexus, but zero RMP data. The existing bulk scraper pages through ALL UCSB teachers on RMP — slow and fetches data we don't need. We need a smarter, targeted approach.

## Decisions

- **Targeted name search:** For each active Nexus professor, search RMP by name + UCSB school filter. Fuzzy match during scraping. Only save matches.
- **Active professors only:** Only scrape professors who taught in 2023-2025 (2,292 of 5,976).
- **Direct to DB:** No intermediate JSON cache. Each professor committed individually for resumability.
- **First 20 comments:** One page of comments per professor — sufficient for VADER sentiment + TF-IDF keywords.
- **Every 2 days:** Scheduler runs scrape + NLP + scoring every 2 days at 2am (not nightly).

## Data Flow

```
Active Professors (2023-2025)      -> 2,292 from Postgres
       |
For each professor name:
  Search RMP GraphQL (name + UCSB)   -> top 5 results
  Fuzzy match (token_sort_ratio)      -> >=85 auto-link, 70-84 review, <70 skip
  Save to DB (professor, rating, 20 comments)
       |
NLP batch pass:
  VADER sentiment on every comment    -> rmp_comments.sentiment_score
  TF-IDF keywords per professor       -> rmp_comments.keywords
       |
Scoring batch pass:
  Compute Gaucho Score per (prof, course) pair -> gaucho_scores table
       |
Dashboard reads everything live
```

## Code Changes

| File | Change |
|------|--------|
| `scrapers/rmp_scraper.py` | Add `search_teacher_by_name()` using name + school GraphQL query |
| `scrapers/rmp_scraper.py` | Add `fetch_active_teachers(session)` — loops active professors, searches by name |
| `scrapers/rmp_loader.py` | Update to set `match_confidence` + link `professor_id` from Nexus match |
| `etl/nlp_processor.py` | Add `process_all_comments(session)` — batch VADER + TF-IDF over DB |
| `etl/scoring.py` | Add `compute_all_scores(session, weights)` — batch score computation |
| `scheduler/jobs.py` | Change cron to every 2 days; use targeted scrape + auto-run NLP + scoring |
| New: `scripts/run_pipeline.py` | One-shot CLI script to run full pipeline (scrape -> NLP -> score) |

## RMP GraphQL Query (Name Search)

```graphql
query TeacherSearchQuery($text: String!, $schoolID: ID!) {
  newSearch {
    teachers(query: {text: $text, schoolID: $schoolID}, first: 5) {
      edges {
        node {
          legacyId
          firstName
          lastName
          department
          avgRating
          avgDifficulty
          wouldTakeAgainPercent
          numRatings
          ratings(first: 20) {
            edges {
              node {
                comment
                date
              }
            }
          }
        }
      }
      pageInfo { hasNextPage endCursor }
    }
  }
}
```

## Fuzzy Matching Rules

- `token_sort_ratio >= 85` -> auto-link, set `match_confidence`
- `token_sort_ratio 70-84` -> save but flag status as "review"
- `token_sort_ratio < 70` -> skip, do not save

Name normalization: strip titles (Dr., Prof., PhD), lowercase, reorder "LAST, FIRST" to "first last".

## Resumability

- Each professor committed individually — partial progress survives interruption
- Next run skips professors with `rmp_ratings.fetched_at` less than 2 days old
- Console progress: `[423/2292] Scraped: Phill Conrad -- match: 95%`

## Schedule

- Every 2 days at 2am: targeted RMP scrape (only stale professors)
- After each scrape: auto-run NLP + scoring
- On-demand: `python scripts/run_pipeline.py`

## Time Estimate

- Initial scrape: ~2,292 requests at ~3s delay = ~115 minutes
- Subsequent runs: only re-fetch stale data, much faster
- NLP + scoring: < 1 minute (batch SQL + in-memory computation)

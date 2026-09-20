# Critical Audit — 2026-09-19

Scope: full repository review plus live audit of https://www.coursepick.app and the
production API at `https://gaucho-course-optimizer.onrender.com`.
No prior reports existed in `docs/audits/`, so this is the baseline audit.
`.planning/codebase/CONCERNS.md` (2026-03-30) was read first; its still-open items are
tracked in the last section, and several of its entries are confirmed fixed.

## Executive summary

The product is in worse shape than the code suggests, because the most serious problems are
data-correctness and integration bugs that unit tests cannot see. During this audit the
production API went **completely down and was still down 40 minutes later** — every database-backed
endpoint returned HTTP 500 while `/health` cheerfully returned `200 {"status":"ok"}`, so
uptime monitoring would have shown green throughout. Independently of the outage, **course
search cannot find any course whose code contains a space**: the grades ingester strips
whitespace when storing codes, but the search endpoint does not strip it from the query, so
"CS 16" — the app's own placeholder example — returns zero results. And the professor
rankings people see are built on name matches as weak as 73% confidence, presented with no
confidence indicator at all, which is the worst failure mode this product has.

Fix first: (1) make `/health` actually check the database and find out why Postgres calls are
failing, (2) normalize whitespace in course search, (3) stop publishing sub-80% name matches
as fact. One thing done well: the `dashboard/queries.py` rewrite genuinely eliminated the N+1
query pattern flagged in the March concerns doc — professor listings now resolve in three
queries with correct per-comment tag deduplication, and connection pooling is properly
configured with `pool_pre_ping`.

A notable pattern worth calling out: the legacy Streamlit app (`dashboard/app.py`) is *more
correct* than the production React app in three separate places — it strips whitespace from
search queries, it applies the Bayesian small-sample adjustment to ratings, and it displays
match confidence to the user. All three behaviours were lost in the React/FastAPI rewrite.

## Findings index

| ID | Title | Category | Severity | Effort | Area |
|----|-------|----------|----------|--------|------|
| BUG-1 | Health check returns OK during total database outage | Bug / Ops | Critical | S | `api/routers/health.py` |
| BUG-2 | Course search fails for any query containing a space | Bug | Critical | S | `dashboard/queries.py` |
| DATA-1 | Sub-80%-confidence professor matches published as fact | Data quality | Critical | M | `scrapers/targeted_scrape.py` |
| BUG-3 | Grade history ordered alphabetically by quarter name | Bug | High | S | `dashboard/queries.py` |
| BUG-4 | Professor tags can never appear — threshold is unreachable | Bug | High | S | `etl/nlp_processor.py` |
| BUG-5 | Bayesian small-sample adjustment missing from live rankings | Bug | High | M | `api/routers/courses.py` |
| BUG-6 | 500 responses carry no CORS headers, so the SPA sees a network error | Bug | High | S | `api/main.py` |
| UX-1 | Search reports "No courses found" when the API is failing | UX | High | S | `frontend/src/components/CourseSearch.tsx` |
| DATA-2 | Truncated Nexus names silently defeat matching for most professors | Data quality | High | L | `etl/name_matcher.py` |
| BUG-7 | All course titles are NULL in production | Bug | High | M | `scrapers/grades_loader.py` |
| BUG-8 | Matcher passes 1 and 3 reuse already-consumed RMP candidates | Bug | Medium | M | `etl/enhanced_matcher.py` |
| BUG-9 | Pass 1 links professors across mismatched departments | Bug | Medium | S | `etl/enhanced_matcher.py` |
| BUG-10 | Ambiguous abbreviated names merged arbitrarily in dedup | Bug | Medium | M | `etl/enhanced_matcher.py` |
| BUG-11 | Falsy-zero checks treat a 0.0 rating as missing data | Bug | Medium | S | `etl/scoring.py` |
| BUG-12 | `normalize_gpa` ignores its own `dept_median` parameter | Bug | Medium | S | `etl/scoring.py` |
| BUG-13 | `/quarters/current` returns 502 in production | Bug | Medium | S | `api/routers/quarters.py` |
| BUG-14 | Registration banner dismissal never expires | Bug | Low | S | `frontend/src/components/RegistrationBanner.tsx` |
| SEC-1 | 13 MB database dump of scraped RMP comments committed to a public repo | Security / Legal | High | S | `data/gco_dump.sql` |
| SEC-2 | No rate limiting on any public endpoint | Security | Medium | M | `api/main.py` |
| ARCH-1 | `scheduled_sections` table has no Alembic migration | Architecture | Medium | S | `db/migrations/` |
| ARCH-2 | `dashboard/` is half dead code and half production dependency | Architecture | Medium | M | `dashboard/` |
| ARCH-3 | Quarter-code derivation duplicated three times, timezone-naive | Architecture | Medium | S | `api/routers/courses.py` |
| PERF-1 | Streamlit, Plotly, pandas and scikit-learn installed on the API host | Performance | Medium | S | `requirements.txt` |
| PERF-2 | Professors endpoint is unpaginated and returns every field | Performance | Medium | M | `api/routers/courses.py` |
| UX-2 | Error state blames the user's connection and offers no retry | UX | Medium | S | `frontend/src/pages/CoursePage.tsx` |
| UX-3 | Sentiment factor is explained incorrectly to users | UX | Medium | S | `frontend/src/pages/HomePage.tsx` |
| UX-4 | No data freshness or source attribution anywhere | UX / Trust | Medium | S | frontend |
| UX-5 | Score is called "Prof Score", "Gaucho Score" and `gaucho_score` | UX | Low | S | frontend / api |
| UX-6 | Stray "Courses" heading renders under the empty state | UX | Low | S | `frontend/src/components/CourseSearch.tsx` |
| A11Y-1 | GPA trend chart has no accessible name or role | A11y | Medium | S | `frontend/src/components/GpaTrendChart.tsx` |
| A11Y-2 | Nested interactive elements: button inside link | A11y | Low | S | `frontend/src/pages/HomePage.tsx` |
| SEO-1 | Both domains serve identical content with no canonical URL | SEO | Medium | S | `frontend/vercel.json` |
| SEO-2 | Every route shares one title and description; no robots.txt | SEO | Medium | M | `frontend/index.html` |
| TEST-1 | No test covers quarter ordering, tag output, or API scoring parity | Testing | Medium | M | `tests/` |
| TEST-2 | CI never runs frontend tests, lint, or type checks; deploys bypass CI | Testing | Medium | S | `.github/workflows/` |

Counts: **3 Critical**, **7 High**, **20 Medium**, **5 Low** (35 findings).

## Findings

### Critical

#### BUG-1: Health check returns OK during total database outage

- **Where:** `api/routers/health.py:7-14`; live evidence against `https://gaucho-course-optimizer.onrender.com`
- **What:** Between roughly 16:53 and at least 17:34 PT on 2026-09-19 — **over 40 minutes** —
  every database-backed endpoint returned HTTP 500 continuously, while `/health` returned
  `200 {"status":"ok"}` the entire time. A minute-by-minute poll from 17:18 to 17:27 recorded
  ten consecutive 500s with no recovery, and a further check at 17:33:44 was still failing, so
  the service does not self-heal. Measured at 17:27:46 PT:

  | Endpoint | Status |
  |---|---|
  | `/health` | 200 (0.15s) |
  | `/courses/search?q=MATH4A` | 500 (0.17s) |
  | `/courses/14397/professors` | 500 (0.19s) |
  | `/quarters/current` | 502 (0.60s) |

  The same endpoints returned 200 at 16:45 PT, so this was a live regression during the
  audit, not a cold start — the sub-200ms response times confirm the app is up and failing
  fast, which points at the database connection or credentials rather than a timeout — a
  suspended or over-quota Neon free-tier branch is the most likely candidate and should be
  checked first. The docstring makes the blindness deliberate: *"Must NOT have Depends(get_db)
  — health check must succeed even during DB downtime."*
- **Impact:** Every user hits a broken site for the entire duration of an outage while
  UptimeRobot reports 100% uptime, so nobody is paged. This is how a 35-minute outage becomes
  a multi-day outage. The root cause of the 500s still needs diagnosis (check Render logs and
  whether the Neon connection string or a suspended free-tier Neon branch is at fault).
- **Suggested fix:** Keep a liveness route that skips the database, but add a separate
  readiness route that runs `SELECT 1` and returns 503 on failure, and point monitoring at
  that one. Distinguishing liveness from readiness is the standard split; the current design
  conflates "the process is running" with "the service works".

#### BUG-2: Course search fails for any query containing a space

- **Where:** `dashboard/queries.py:115-124` versus `scrapers/grades_ingester.py:23-25`
- **What:** Course codes are normalized at ingest time by stripping all whitespace:

```23:25:scrapers/grades_ingester.py
def normalize_course_code(code: str) -> str:
    """Remove all whitespace from a course code."""
    return "".join(code.split())
```

  The search path never applies the same normalization, so it ILIKEs the raw query against
  space-free stored codes. Verified live against the API:

  | Query | Results |
  |---|---|
  | `MATH4A` | 2 |
  | `MATH 4A` | 0 |
  | `CHEM 1A` | 0 |
  | `CS 16` | 0 |
  | `Physics` | 0 |

  This is not a subtle edge case: the search box placeholder reads *"Search courses by name
  or code (e.g., CS 16, Physics)"*, the homepage instructs users to type `"CMPSC 130A"`, and
  the empty state advises *"Try a different course name or code. Example: 'CS 16' or
  'Physics 1'"* — every one of those suggestions returns nothing. The legacy Streamlit app
  already solved this at `dashboard/app.py:84` with
  `_search_courses(search_query.replace(" ", ""))`; the fix was lost in the API rewrite.
  Screenshot: `coursepick-search-cs16-no-results-during-500.png` shows the dead end.
- **Impact:** Students type course codes the way the university writes them, with a space.
  For those users the product appears to contain no data at all. This is plausibly the single
  largest source of silent abandonment.
- **Suggested fix:** Strip whitespace from the query in `search_courses` before building the
  ILIKE pattern, matching the ingest normalization. Also relax the endpoint's regex so it
  isn't the thing rejecting valid input, and add a test asserting `"CS 16"` and `"CMPSC16"`
  return the same course.

#### DATA-1: Sub-80%-confidence professor matches published as fact

- **Where:** `scrapers/targeted_scrape.py:75-88`
- **What:** The targeted scraper accepts any fuzzy name match at 70% or above, labels
  everything below 85% as `"review"`, and then writes it straight to the database anyway:

```75:82:scrapers/targeted_scrape.py
        if best_match and best_confidence >= 70:
            status = "auto" if best_confidence >= 85 else "review"
            try:
                load_rmp_teacher_to_db(
                    best_match, session,
                    nexus_professor_id=prof_id,
                    match_confidence=best_confidence,
                )
```

  There is no review queue and no gate — `"review"` is a log string. The live consequences for
  MATH4A (course id 14397), from the production API response: of 16 professors with RMP data,
  **9 were matched below 80% confidence** and only 3 reached the 85% "auto" bar. The
  top-ranked professor students are steered toward is a 73% match:

  | Score | Confidence | RMP ratings | Name |
  |---|---|---|---|
  | 83.12 | 73% | 5 | Charles Kulick |
  | 77.81 | 85% | 30 | Jon McCammond |
  | 76.81 | 74% | 11 | Troy Kling |
  | 75.50 | 76% | 28 | Rhea Bakshi |
  | 74.19 | 77% | 251 | Peter Garfield |

  The matching itself is fragile enough to make this dangerous. `match_confidence` is
  `fuzz.token_sort_ratio` over normalized full names, which scores short Chinese, Korean and
  Vietnamese name pairs far above the 70% floor even when they are different people —
  approximating with `difflib`, `"li wei"` vs `"wei liu"` scores 92 and `"chen eric"` vs
  `"erica chen"` scores 95. `ProfessorCard.tsx` renders the rating, difficulty, "would take
  again" percentage and student comments with no confidence indicator, while the legacy
  Streamlit app did show it (`dashboard/app.py:140-141`, `Match: {confidence}%`).
- **Impact:** Students choose classes based on another person's reviews, and named professors
  have inaccurate ratings and student comments attributed to them on a public site. That is
  both the product's core value proposition inverted and a reputational risk to real people.
- **Suggested fix:** Raise the write threshold to 85 and route 70–84 into a review table that
  the API does not serve, or at minimum surface confidence in the UI and visually de-emphasize
  low-confidence matches. Constrain candidates by last name and department before scoring, and
  require a surname match rather than letting a whole-string ratio carry the decision.

### High

#### BUG-3: Grade history ordered alphabetically by quarter name

- **Where:** `dashboard/queries.py:289-293`
- **What:** `get_grade_history` orders by the quarter text column, so quarters sort
  alphabetically — Fall, Spring, Summer, Winter — rather than chronologically:

```289:293:dashboard/queries.py
    grades = (
        session.query(GradeDistribution)
        .filter_by(professor_id=professor_id, course_id=course_id)
        .order_by(GradeDistribution.year, GradeDistribution.quarter)
        .all()
    )
```

  Verified live: professor "CHEN E" for MATH4A returned
  `['Fall 2019', 'Fall 2020', 'Spring 2020']`. Note that the same file already contains the
  correct ordering helper for a different query — `quarter_order = {"Fall": 4, "Summer": 3,
  "Spring": 2, "Winter": 1}` at line 221 — so the knowledge exists and simply isn't applied
  here. Two consumers then compound the error: `GradeChart.getFilteredQuarters` treats the
  last array element as "most recent" (`GradeChart.tsx:23-25`), and `GpaTrendChart` plots the
  array order straight onto the x-axis.
- **Impact:** The default grade distribution chart shows the wrong quarter whenever a
  professor taught more than one quarter in a year, and the GPA trend line plots time out of
  order, which makes trends look like noise.
- **Suggested fix:** Store a sortable quarter ordinal, or map quarter names to the existing
  ordinal in the query and sort by `(year, ordinal)`. Add a regression test with Spring and
  Fall in the same year.

#### BUG-4: Professor tags can never appear — threshold is unreachable

- **Where:** `etl/nlp_processor.py:78-82` and `dashboard/queries.py:243-263`
- **What:** Keyword extraction stores the result on exactly one comment row per rating:

```78:82:etl/nlp_processor.py
        if len(texts) >= 2:
            keywords = extract_keywords(texts, top_n=8)
            # Store keywords on the first comment of this rating
            comments_for_rating[0].keywords = keywords
            stats["keywords_set"] += 1
```

  The tag aggregator then treats each comment's keyword list as one "vote", deduplicating
  within a comment, and finally filters with `min_count=3`. Because only one comment per
  rating ever carries keywords, every tag can accumulate at most **one** vote, so the
  `count >= 3` filter always empties the list. Confirmed against production: **0 of 55**
  professors returned for MATH4A had a non-empty `tags` array. The ~60-line curated
  `TAG_VOCABULARY` in `dashboard/queries.py:18-77` and the `ProfessorCard` tag rendering at
  lines 207-219 are entirely unreachable.
- **Impact:** A built, tested and shipped feature produces nothing in production, and the
  professor cards lose their most scannable qualitative signal. It is also invisible — nothing
  errors, the tags are just always absent.
- **Suggested fix:** Decide where the unit of counting lives. Either run VADER/TF-IDF keyword
  extraction per comment and store keywords on every comment row, or aggregate tags from raw
  comment text at query time. Then set `min_count` relative to the actual number of comments.
  A test asserting at least one tag for a professor with many similar comments would have
  caught this.

#### BUG-5: Bayesian small-sample adjustment missing from live rankings

- **Where:** `api/routers/courses.py:89-98` versus `etl/scoring.py:134-137`
- **What:** The batch scorer shrinks ratings toward a 3.0 prior for professors with few
  reviews, which is the statistically necessary correction:

```134:137:etl/scoring.py
        # Bayesian adjust quality factor
        if quality and num_ratings:
            adj_qual = bayesian_adjust(quality, num_ratings, 3.0)
            qual_f = normalize_quality(adj_qual)
```

  The endpoint that actually serves the website recomputes factors from scratch and omits
  that step entirely, passing raw quality straight into `compute_gaucho_score`. The frontend
  then re-derives scores from the same unadjusted factors in `lib/scoring.ts`. Live effect on
  MATH4A: Charles Kulick, with **5 ratings** averaging 5.0, outranks Peter Garfield, who has
  **251 ratings** — 83.12 versus 74.19. With the adjustment Kulick's quality would shrink
  toward the prior and the ordering would likely flip. The legacy Streamlit app applies the
  adjustment (`dashboard/app.py:115-117`), so this too regressed in the rewrite.

  Related: `compute_all_scores` writes the `gaucho_scores` table on every pipeline run, but
  no API route reads it. The table, its unique constraint and its two indexes are dead weight,
  and its scores disagree with what the site displays.
- **Impact:** Rankings systematically favour professors with almost no reviews, which is
  exactly the population whose averages are least trustworthy. A student following the top
  recommendation is often following five people's opinions over 251.
- **Suggested fix:** Extract one scoring function used by the endpoint, the batch job and
  (via identical logic) the frontend, so the adjustment cannot be omitted in one path. Then
  either serve the precomputed `gaucho_scores` rows or delete the table.

#### BUG-6: 500 responses carry no CORS headers, so the SPA sees a network error

- **Where:** `api/main.py:12-17`
- **What:** FastAPI's unhandled-exception handler runs outside `CORSMiddleware`, so error
  responses ship without `Access-Control-Allow-Origin`. Compared directly with an `Origin`
  header set:

  - `/health` → `200`, includes `access-control-allow-origin: https://www.coursepick.app`
  - `/courses/search?q=MATH4A` → `500`, **no** CORS headers at all

  From inside the live page, the browser therefore cannot read the status. A fetch executed
  on `coursepick.app` returned `{"error":"TypeError: Failed to fetch","ms":127}` — an opaque
  network failure, not a 500.
- **Impact:** The frontend cannot distinguish a server fault from an offline client, which is
  precisely why UX-1 and UX-2 show misleading messages. It also makes production debugging
  from browser telemetry nearly impossible.
- **Suggested fix:** Add an exception handler that returns a JSON error through the middleware
  stack (or wrap the app so CORS headers are attached to error responses), and include a
  correlation id in the body for log lookup.

#### UX-1: Search reports "No courses found" when the API is failing

- **Where:** `frontend/src/components/CourseSearch.tsx:16, 30-37`; `frontend/src/hooks/useCourseSearch.ts:5-9`
- **What:** The component destructures only `data` and `isLoading` and never inspects `error`:

```16:16:frontend/src/components/CourseSearch.tsx
  const { data: courses, isLoading } = useCourseSearch(query)
```

  When the request fails, `courses` is undefined and the component falls through to
  `CommandEmpty`, which renders *"No courses found — Try a different course name or code."*
  Captured live during the BUG-1 outage: searching `CS 16` displayed the no-results state
  even though the API was returning 500 on every call. Screenshot:
  `coursepick-search-cs16-no-results-during-500.png`.
- **Impact:** During a complete backend outage the site confidently tells students that UCSB
  does not offer the course they searched for. Users conclude the data is missing and leave,
  and no one reports an outage.
- **Suggested fix:** Handle `isError` with a distinct message and a retry action, and keep it
  visually separate from the empty state. Given BUG-6, fix the CORS issue too or the frontend
  cannot tell the two situations apart.

#### DATA-2: Truncated Nexus names silently defeat matching for most professors

- **Where:** `etl/name_matcher.py:23-25`, `etl/name_utils.py:6-36`; production data
- **What:** Daily Nexus instructor names arrive abbreviated and truncated to roughly 13
  characters. Real examples from the committed dump and the live API: `CASTELLA-CABE`,
  `ALONSO RODRIG`, `PORTER M J`, `JEVBRATT L V`, `SVADLENAK N D`. Matching compares these to
  full RMP names with `token_sort_ratio` and a 70/85 threshold, which truncation pushes well
  below the floor — approximating with `difflib`, `"castella-cabe"` vs
  `"ana castellanos cabrera"` scores 44 and `"alonso rodrig"` vs `"maria alonso rodriguez"`
  scores 74. Two further systematic gaps: `parse_nexus_name` always takes the *first* token as
  the surname, while the RMP side indexes on the *last* token
  (`enhanced_matcher.py:118-121`), so multi-word surnames like "VAN DER BERG" key on `van`
  against `berg` and can never meet; and truncation can sever a surname mid-word so no
  exact-key lookup succeeds. Measured impact on MATH4A: **39 of 55 professors (71%) have no
  RMP data at all** and are scored with neutral 0.5 placeholders.
- **Impact:** Most professors are unrankable on three of the four advertised factors, and
  because missing factors default to 0.5 they receive a middling score (~60) that looks like a
  real measurement rather than "unknown". It also skews rankings: a professor with genuinely
  poor reviews but no match can outrank a matched professor with mediocre reviews.
- **Suggested fix:** Match on a prefix/surname basis appropriate to truncated input — compare
  the truncated string as a prefix of the RMP surname plus initial, rather than whole-string
  fuzzy ratio — and index candidates by both first and last token. Separately, distinguish
  "no data" from "neutral" in the score so unmatched professors aren't presented as average.

#### BUG-7: All course titles are NULL in production

- **Where:** `dashboard/queries.py:115-124`; `db/models.py:31`; live API
- **What:** `search_courses` ORs the query against `Course.code` and `Course.title`, but every
  title in production is null. A search for `MATH` returned 20 results with **20 null
  titles**, and the earlier `Calculus` and `Physics` searches returned nothing. The Daily
  Nexus CSV path never populates the column, so half the search predicate is inert.
- **Impact:** Title search — explicitly promoted on the homepage ("or 'Introduction to
  Algorithms'") — cannot work. Results lists show bare codes like `MATH100A`, so students who
  don't already know the code cannot identify the course, and the search page looks broken for
  natural-language queries.
- **Suggested fix:** Backfill titles from the UCSB Academic Curriculums API, which the project
  already integrates and which returns `title` per course (`ucsb_api/client.py:100`), then keep
  them fresh in the nightly sync. Until titles exist, drop the misleading homepage copy.

#### SEC-1: 13 MB database dump of scraped RMP comments committed to a public repo

- **Where:** `data/gco_dump.sql`, added in commit `10807f8`
- **What:** `.gitignore` lists `data/`, but the file was committed before that rule and
  ignore rules do not untrack existing files — `git ls-files data/` confirms it is tracked.
  The dump is 13,132,038 bytes / 147,656 lines and contains full `COPY` blocks for
  `professors`, `courses`, `grade_distributions`, `rmp_ratings` and `rmp_comments`. The
  GitHub repository responds 200 unauthenticated, so this is public. Sample rows include
  verbatim student-written RateMyProfessors comments tied to named professors, e.g.
  `good teacher- pretty hot.` and comments naming individual TAs. No database credentials
  appear in the file (checked).
- **Impact:** This republishes a third party's user-generated content in bulk, which is
  squarely against RateMyProfessors' terms, and attaches unflattering personal remarks about
  named individuals to your GitHub account outside the context they were written in. It also
  bloats every clone and, because `alembic_version` in the dump is `3ee0c9e2add3` with no
  `scheduled_sections` table, it is stale enough to be misleading as a restore artifact.
- **Suggested fix:** Remove the file from history (`git filter-repo`) and distribute a small
  synthetic fixture for local development instead. If a real snapshot is needed, keep it in
  private object storage. The `scripts/export_db.sh` / `import_db.sh` pair can stay.

### Medium

#### BUG-8: Matcher passes 1 and 3 reuse already-consumed RMP candidates

- **Where:** `etl/enhanced_matcher.py:113-153` (pass 1), `229-272` (pass 3), versus `203` (pass 2)
- **What:** Pass 2 explicitly removes a linked RMP professor from the candidate pool so it
  cannot be claimed twice (`rmp_profs.remove(best_rmp)`). Passes 1 and 3 build a
  `rmp_by_last` index up front and never prune it, even though `_link_professor` *deletes* the
  RMP-only row it consumed (`enhanced_matcher.py:91`). Because duplicate abbreviated Nexus
  rows genuinely exist — that is the entire reason pass 4 exists — a second Nexus professor
  with the same surname and initial can be handed the same, now-deleted candidate. The
  collision guard reads `rmp_prof.rmp_id` on a deleted, expired instance, which either raises
  or degrades into an `IS NULL` comparison that silently returns a false collision. The
  inconsistency between passes is itself the evidence that pruning is required.
- **Impact:** Nondeterministic matching outcomes across runs, and in the degraded path a
  legitimate match is silently skipped. Because all four passes commit as they go, a failure
  mid-pipeline leaves the database partially matched.
- **Suggested fix:** Track consumed RMP ids in a set shared across all passes and filter
  candidates against it, mirroring pass 2. Add an end-to-end test running all four passes over
  a fixture containing duplicate abbreviated names.

#### BUG-9: Pass 1 links professors across mismatched departments

- **Where:** `etl/enhanced_matcher.py:140-147`
- **What:** When exactly one RMP professor shares a surname and first initial, pass 1 links it
  regardless of department, recording confidence 90 on a department match and 75 otherwise:

```140:143:etl/enhanced_matcher.py
            dept_match = departments_match(prof.department, rmp_prof.department)
            confidence = 90.0 if dept_match else 75.0
```

  A surname plus one initial is weak evidence — "HUANG L" in Mathematics will link to a
  "Lisa Huang" in Art Studio if she is the only Huang whose first name starts with L. Note
  `departments_match` returns `False` whenever either department is missing
  (`department_mapper.py:92-93`), so absent metadata is indistinguishable from a real mismatch
  and lands in the same 75 bucket.
- **Impact:** Cross-department false matches enter the database with confidence values that
  DATA-1 then publishes as fact.
- **Suggested fix:** Require a department match for initial-only links, or defer non-matching
  candidates to a review queue rather than writing them at 75.

#### BUG-10: Ambiguous abbreviated names merged arbitrarily in dedup

- **Where:** `etl/enhanced_matcher.py:305-350`; `etl/name_utils.py:72-86`
- **What:** `find_duplicate_pairs` returns the cross product of initial-only and full-name
  professors sharing a surname and department, so "SMITH J" pairs with both "SMITH JOHN" and
  "SMITH JANE". Pass 4 iterates those pairs and transfers all of the abbreviated professor's
  grade distributions into whichever full-name professor it encounters first, then deletes the
  abbreviated row. The second pairing then no-ops because the row is gone — so the ambiguity
  is resolved by iteration order with no guard and no warning.
- **Impact:** One professor's grade distributions are permanently reattributed to a
  same-surname colleague, and the merge is irreversible. This corrupts the GPA factor for both
  professors, and unlike a matching error it cannot be detected downstream.
- **Suggested fix:** Skip merges where an abbreviated name matches more than one full name in
  the same department, and log them for manual resolution. Group pairs by abbreviated id and
  assert exactly one candidate before mutating.

#### BUG-11: Falsy-zero checks treat a 0.0 rating as missing data

- **Where:** `etl/scoring.py:129-131`; `dashboard/queries.py:270-271`; `dashboard/app.py:109-111`
- **What:** Several factor computations guard with truthiness rather than a null check:

```129:131:etl/scoring.py
        gpa_f = normalize_gpa(float(mean_gpa)) if mean_gpa else 0.5
        qual_f = normalize_quality(quality) if quality else 0.5
        diff_f = normalize_difficulty(difficulty) if difficulty else 0.5
```

  A genuine `0.0` — a 0.0 average GPA, or a 0.0 RMP quality — is falsy, so it is replaced by
  the neutral 0.5 placeholder. Note the same file handles sentiment correctly with
  `is not None` on the next line, and `api/routers/courses.py:90-96` uses explicit
  `is not None` checks, so the codebase is internally inconsistent. `dashboard/queries.py:270`
  has the mirror-image bug, rounding `mean_gpa` only when truthy and otherwise reporting
  `None`.
- **Impact:** The worst-performing professors are scored as average, inverting the ranking
  exactly where it matters most. Rare, but wrong in the most misleading direction.
- **Suggested fix:** Use `is not None` consistently for every nullable numeric factor, and add
  a scoring test with 0.0 inputs.

#### BUG-12: `normalize_gpa` ignores its own `dept_median` parameter

- **Where:** `etl/scoring.py:1-6`
- **What:** The signature promises department-relative normalization but the body never reads
  `dept_median`:

```1:6:etl/scoring.py
def normalize_gpa(gpa: float, dept_median: float = 3.0, dept_max: float = 4.0) -> float:
    """Normalize GPA to 0-1 relative to department stats."""
    if dept_max == 0:
        return 0.0
    return max(0.0, min(1.0, gpa / dept_max))
```

  The docstring's claim of normalizing "relative to department stats" is false. The legacy
  Streamlit app computes a department median and passes it (`dashboard/app.py:107-109`),
  believing it matters; it is silently discarded.
- **Impact:** GPA is compared on a raw 0–4 scale across departments, so professors in
  historically lenient departments score higher on the GPA factor for reasons unrelated to
  their teaching. Within a single course page all professors share a department, so ranking is
  mostly unaffected — but the absolute score is not comparable across courses, which is how
  the 0–100 number is presented.
- **Suggested fix:** Either implement the intended normalization (e.g. centre on the
  department median) or delete the parameter and correct the docstring. A dead parameter that
  callers deliberately populate is worse than none.

#### BUG-13: `/quarters/current` returns 502 in production

- **Where:** `api/routers/quarters.py:33-77`; live API
- **What:** `GET /quarters/current` returned
  `502 {"detail":"Failed to fetch quarter info from UCSB API"}` in 0.6s, both before and
  during the BUG-1 outage, so it is an independent failure — most likely a missing or expired
  `UCSB_API_KEY` on Render (a missing key yields 503, so the key is present but the upstream
  call fails). `useQuarterInfo` retries once and `RegistrationBanner` returns `null` on any
  error, so the failure is completely invisible.
- **Impact:** The registration countdown — the feature most likely to bring students back at
  pass-time — never renders, and nothing signals that it is broken. The nightly schedule sync
  uses the same client, so scheduled-section data may be going stale for the same reason.
- **Suggested fix:** Verify the key against the UCSB API and log the upstream status code
  rather than collapsing every failure into one 502 string. Consider caching the last good
  calendar response so a transient upstream failure doesn't blank the banner.

#### SEC-2: No rate limiting on any public endpoint

- **Where:** `api/main.py:6-22`
- **What:** No rate-limiting middleware is registered and no reverse-proxy limit is
  configured. The expensive endpoint is unauthenticated and trivially enumerable:
  `/courses/{id}/professors` runs a multi-join aggregate plus two schedule queries and
  returned ~26 KB for 55 professors. Course ids are sequential integers, so the entire dataset
  can be walked. Positives worth noting: the search endpoint constrains input with
  `pattern=r"^[a-zA-Z0-9 \-]+$"`, which I verified rejects `%` and `_` with 422 and thereby
  blocks ILIKE wildcard abuse, and all queries go through the ORM rather than string
  concatenation.
- **Impact:** A single client can saturate the free-tier Render instance and the Neon
  connection pool (`pool_size=5, max_overflow=10`), causing an outage for everyone, or scrape
  the whole database cheaply.
- **Suggested fix:** Add per-IP limiting (SlowAPI, or Cloudflare rules since traffic already
  passes through Cloudflare) on the professors and search endpoints, and set a short
  `Cache-Control` on responses so repeat reads don't reach Postgres.

#### ARCH-1: `scheduled_sections` table has no Alembic migration

- **Where:** `db/models.py:111-135`; `db/migrations/versions/`
- **What:** `ScheduledSection` is defined in the models with a unique constraint and two
  foreign keys, but neither migration creates it — the initial schema predates it and
  `1fd97b94581d_add_fk_indexes.py` only touches pre-existing tables. Confirmed by grepping
  both migration files and by the committed dump, whose `alembic_version` is `3ee0c9e2add3`
  and which contains no `scheduled_sections` table. The production table must therefore have
  been created by `create_all` or by hand.
- **Impact:** `alembic upgrade head` on a fresh database produces a schema the application
  cannot run against, so disaster recovery and any new environment are broken. Its foreign
  keys also missed the index migration, so `professor_id` and `course_id` lookups — used on
  every course page via `get_scheduled_sections` — likely sequential-scan.
- **Suggested fix:** Autogenerate a migration for `scheduled_sections` including indexes on
  `professor_id`, `course_id` and `quarter_code`, then verify `upgrade head` from empty
  reproduces production. Adding a CI job that migrates an empty database and compares against
  the models would prevent recurrence.

#### ARCH-2: `dashboard/` is half dead code and half production dependency

- **Where:** `dashboard/app.py`, `dashboard/queries.py`, `api/routers/courses.py:8`, `docker-compose.yml`
- **What:** The Streamlit UI is superseded by the React frontend, yet `docker-compose.yml`
  still declares it as the primary service. Meanwhile `dashboard/queries.py` is *live
  production code* — every FastAPI router imports from it:
  `from dashboard.queries import get_all_course_sections, get_professors_for_course, ...`.
  So the package named after the dead UI holds the real data-access layer, while the dead UI
  beside it duplicates scoring logic that has since diverged (and, per BUG-2, BUG-5 and
  DATA-1, is in several respects more correct than production).
- **Impact:** Anyone deleting `dashboard/` to remove the legacy app breaks the entire API. The
  duplicated scoring logic is an active source of the divergence bugs in this report, and
  `docker-compose up` gives new contributors the obsolete interface.
- **Suggested fix:** Move `queries.py` to a neutral package (`db/queries.py` or
  `api/queries.py`), delete `dashboard/app.py` and its compose service, and drop Streamlit and
  Plotly from `requirements.txt` (see PERF-1).

#### ARCH-3: Quarter-code derivation duplicated three times, timezone-naive

- **Where:** `api/routers/courses.py:61-73`, `api/routers/courses.py:139-151`, `scheduler/jobs.py:76-89`
- **What:** The same month-to-quarter heuristic is copy-pasted in three places:

```65:72:api/routers/courses.py
    if month <= 3:
        current_qcode = f"{year}1"  # Winter
    elif month <= 6:
        current_qcode = f"{year}2"  # Spring
    elif month <= 8:
        current_qcode = f"{year}3"  # Summer
    else:
        current_qcode = f"{year}4"  # Fall
```

  Two problems beyond the duplication. It uses `date.today()`, which on Render resolves in
  UTC, so for the last seven hours of any quarter-boundary day the server is already in the
  next quarter while California is not. And the project already has an authoritative source
  for this — `UCSBApiClient.fetch_current_quarter()` — which this code bypasses, so the
  heuristic can disagree with the registration banner that does use the API.
- **Impact:** Around quarter boundaries the "Teaching Next Quarter" badge and the scheduled
  sections panel can show the wrong quarter, and the nightly sync can populate a different
  quarter than the API serves. Being wrong for a few hours a quarter is minor; being wrong
  inconsistently across three call sites is the maintenance risk.
- **Suggested fix:** Extract one helper in `ucsb_api/client.py` that prefers the live calendar
  API and falls back to a `ZoneInfo("America/Los_Angeles")`-aware heuristic, and call it from
  all three sites.

#### PERF-1: Streamlit, Plotly, pandas and scikit-learn installed on the API host

- **Where:** `requirements.txt`
- **What:** A single `requirements.txt` serves the API, the ETL pipeline and the legacy
  dashboard, so the Render web service installs `streamlit`, `plotly`, `pandas`,
  `scikit-learn`, `vaderSentiment`, `thefuzz[speedup]`, `curl_cffi` and `apscheduler` — none
  of which the FastAPI process imports at runtime.
- **Impact:** Every Render free-tier cold start pays to import a much larger dependency tree
  than needed, directly worsening the 15–30 second wait the UI has to apologise for, and the
  image is far larger than necessary. Larger attack surface too.
- **Suggested fix:** Split into `requirements-api.txt` (FastAPI, uvicorn, SQLAlchemy, psycopg2,
  pydantic-settings, requests) and `requirements-etl.txt`, and point the Render build at the
  API file.

#### PERF-2: Professors endpoint is unpaginated and returns every field

- **Where:** `api/routers/courses.py:42-127`
- **What:** `/courses/{id}/professors` returns every professor who ever taught the course with
  no `limit`, `offset` or total count, and each record carries all four raw factors, all RMP
  fields, `recent_quarters`, `tags` and fully expanded `scheduled_sections`. Measured live:
  **25,977 bytes for 55 professors** on MATH4A, of whom 39 have no RMP data and are padded
  with 0.5 placeholders. Large enrollment courses will be substantially bigger. The endpoint
  also issues two extra schedule queries per request (current and next quarter) and sorts in
  Python.
- **Impact:** Slow first paint on mobile connections, and the payload grows without bound as
  more historical quarters are ingested. The client must download every professor to display
  the top few.
- **Suggested fix:** Paginate with a default limit, and split the heavy per-professor extras
  (sections, recent quarters) into the detail request that already fires when a card expands.
  The raw factors do need to ship for client-side re-ranking, so keep those.

#### UX-2: Error state blames the user's connection and offers no retry

- **Where:** `frontend/src/pages/CoursePage.tsx:186-191`
- **What:** Any professors-fetch failure renders *"Could not load professors. Check your
  connection and try refreshing."* Captured live during the BUG-1 outage — screenshot
  `coursepick-course-page-error-state-during-outage.png` — while the server was returning 500
  and the user's connection was fine. There is no retry button, no indication the problem is
  server-side, and the weight toggles and filters beside it remain fully interactive despite
  having no data to act on. A related detail: `useProfessors` inherits `retry: 3` from
  `main.tsx:12` with no cap, so four requests fail before the message appears.
- **Impact:** Users are told to fix something they cannot fix, so they refresh repeatedly or
  leave, and outages generate no reports.
- **Suggested fix:** Distinguish server errors from network errors once BUG-6 is fixed, provide
  an explicit retry button wired to `refetch`, and disable the ranking controls while there is
  no data.

#### UX-3: Sentiment factor is explained incorrectly to users

- **Where:** `frontend/src/pages/HomePage.tsx:43-49`
- **What:** The homepage defines the sentiment factor as *"Percentage of recent student
  comments that express a positive experience"* with *"Example: 72% positive"*. It is
  actually the mean VADER compound score over a professor's comments, linearly remapped from
  [-1, 1] to [0, 1] (`api/routers/courses.py:96`). Those are different quantities: a professor
  whose comments are uniformly mildly positive and one with equal numbers of glowing and
  scathing comments can produce the same number, and no percentage of comments is ever
  computed. The `Difficulty` card has a milder version of the same issue, describing "how hard
  students find the workload" when the input is RMP's difficulty rating.
- **Impact:** The one place the methodology is explained describes a different metric than the
  one being shown, which undermines the score's credibility precisely for the careful users
  most likely to read it.
- **Suggested fix:** Describe it as average sentiment of recent reviews on a positive-negative
  scale, or actually compute the share of comments above a positivity threshold, which is what
  users find intuitive and what `SentimentBadge` already does per comment.

#### UX-4: No data freshness or source attribution anywhere

- **Where:** frontend — `HomePage.tsx`, `CoursePage.tsx`, `Layout.tsx`
- **What:** Nothing in the UI states where the data comes from or how current it is. Grade
  distributions originate from the Daily Nexus `grades-data` repository
  (`grades_ingester.py:74`) and ratings from RateMyProfessors, neither of which is credited.
  There is no "last updated" timestamp, even though the data supports it —
  `RmpRating.fetched_at` and `GauchoScore.computed_at` both exist, and the RMP refresh runs
  every two days while grades update quarterly. The audit also found MATH4A grade data ending
  at Fall 2022 for some professors, with no indication to the user that a professor's numbers
  may be four years old. There is no footer and no about/methodology page.
- **Impact:** A student deciding between professors has no way to judge whether they are
  looking at current information, and the site reads as an anonymous scraper rather than a
  credible tool. This is the cheapest available credibility win.
- **Suggested fix:** Add a footer with source attribution and a "ratings updated {date} ·
  grades through {quarter}" line fed by the existing timestamp columns, plus a short
  methodology page explaining the score and its limitations (including match confidence, per
  DATA-1).

#### A11Y-1: GPA trend chart has no accessible name or role

- **Where:** `frontend/src/components/GpaTrendChart.tsx:16-23` versus `GradeChart.tsx:52-55`
- **What:** `GradeChart` is wrapped correctly in a `<figure role="img">` with a descriptive
  `aria-label`. `GpaTrendChart` renders a bare `ResponsiveContainer`, so a screen reader
  encounters an unlabeled SVG with no textual equivalent and no data table. The `<h4>GPA
  Trend</h4>` heading sits outside the chart and is not programmatically associated with it.
  Confirmed by the accessibility snapshot of the course page, where no chart role appears.
- **Impact:** The GPA trend is entirely unavailable to screen reader users, and since the
  trend is one of the two pieces of evidence behind the GPA factor, that is a substantive
  loss rather than decoration.
- **Suggested fix:** Mirror the `GradeChart` pattern — wrap in `<figure role="img">` with an
  `aria-label` summarising direction and range, and add a visually hidden table of
  quarter/GPA pairs.

#### SEO-1: Both domains serve identical content with no canonical URL

- **Where:** `frontend/vercel.json`; live headers
- **What:** `https://www.coursepick.app` and `https://gaucho-course-optimizer.vercel.app`
  return byte-identical HTML — same `etag: "b8784d6c058aaa471e728da5eca2ab86"`, same
  `content-length: 1507` — with no `<link rel="canonical">` anywhere. The apex domain does
  redirect correctly (`https://coursepick.app` → 307 → `https://www.coursepick.app/`), but the
  Vercel subdomain does not. Additionally `og:url` points at the apex, which redirects.
- **Impact:** Two indexable copies of the site compete for the same queries and split link
  equity, so neither ranks as well as one would. For a product students discover by searching
  "UCSB professor grades", organic search is the main acquisition channel.
- **Suggested fix:** Add a canonical link tag pointing at `https://www.coursepick.app`, and
  either redirect the `vercel.app` domain to it or mark it `noindex` via Vercel headers. Point
  `og:url` at the canonical www host.

#### SEO-2: Every route shares one title and description; no robots.txt

- **Where:** `frontend/index.html:13-28`; live
- **What:** The static HTML hardcodes `<title>CoursePick</title>` and the description "Find
  the best professor for any course." for every route. Client-side `document.title` updates
  exist (`CoursePage.tsx:92-94` sets "Course Results | CoursePick") but crawlers and social
  unfurlers reading the served HTML never see them — and "Course Results" carries no course
  name anyway, because the code is passed via router state and is absent on direct navigation
  (the same reason the breadcrumb showed a generic "Course Results" on my deep-link test).
  There is no `robots.txt` and no real sitemap: both `/robots.txt` and `/sitemap.xml` return
  200 with the SPA's `index.html`, because `vercel.json` rewrites `/(.*)` to `/index.html`.
  Serving HTML at those paths is worse than 404ing, since crawlers may treat the malformed
  response as a directive.
- **Impact:** No course page can rank for its own course code, and every shared link previews
  identically as "CoursePick — Find the best professor for any course." Course-code searches
  are exactly the high-intent queries this product should own.
- **Suggested fix:** Add static `public/robots.txt` and a generated `sitemap.xml` (Vercel
  serves `public/` files ahead of rewrites), include the course code in the URL or fetch it on
  load so titles and breadcrumbs are correct on deep links, and consider prerendering course
  pages for per-route meta tags.

#### TEST-1: No test covers quarter ordering, tag output, or API scoring parity

- **Where:** `tests/`, `frontend/src/**/*.test.tsx`
- **What:** Coverage is broad but misses the integration seams where every Critical and High
  finding in this report lives. Specifically: no test asserts the chronological ordering of
  `get_grade_history` (BUG-3) — `tests/test_dashboard_queries.py` exercises quarter data but
  never ordering across quarters within a year; no test asserts that a professor ever receives
  a non-empty `tags` list (BUG-4), so an unreachable threshold went unnoticed; nothing compares
  the API's per-request scoring against `etl/scoring.compute_all_scores`, which is exactly the
  divergence in BUG-5; and no test feeds a spaced course code to `search_courses` (BUG-2). The
  frontend has a `scoring.test.ts` covering weight normalization, but nothing asserting that
  the rendered ranking order matches recomputed scores.
- **Impact:** The suite passes while the product ships wrong data, which is the worst kind of
  green build — it actively discourages the manual verification that would catch these.
- **Suggested fix:** Add contract tests at the seams rather than more unit tests: search
  normalization, grade-history ordering, tag presence end-to-end, and a parity test asserting
  the endpoint and the batch scorer agree for identical inputs.

#### TEST-2: CI never runs frontend tests, lint, or type checks; deploys bypass CI

- **Where:** `.github/workflows/test.yml`
- **What:** CI installs `requirements-dev.txt` and runs `pytest -v` against a Postgres
  service — and nothing else. There is no `npm test` step, so the vitest suite in
  `frontend/src` never runs in CI; no `eslint`; no `tsc --noEmit` (type errors surface only
  in `npm run build`); and no Alembic check (which is why ARCH-1 went unnoticed). Vercel and
  Render both deploy on push to `master` independently of this workflow, so a red build does
  not block a release.
- **Impact:** Frontend regressions reach production unchecked, and a failing test suite cannot
  stop a deploy. The two other workflows (nightly schedule sync, weekly `pg_dump` backup) are
  well built by comparison, which makes the gap look accidental rather than intentional.
- **Suggested fix:** Add a frontend job running `npm ci && npm run lint && tsc -b && npm test`,
  add a migration check that upgrades an empty database and diffs against the models, and gate
  the Vercel/Render deploys on the workflow (Vercel's "ignored build step" or a deploy hook
  triggered from CI).

### Low

#### BUG-14: Registration banner dismissal never expires

- **Where:** `frontend/src/components/RegistrationBanner.tsx:24-34`
- **What:** The dismissal is stored with the quarter code so it can expire when the quarter
  changes, but the check only verifies that the field *exists*:

```29:30:frontend/src/components/RegistrationBanner.tsx
      const parsed = JSON.parse(stored)
      return parsed.dismissed === true && parsed.quarterCode !== undefined
```

  It never compares `parsed.quarterCode` against the current `quarterInfo.next_quarter_code`,
  so the comment "Dismiss expires when the quarter changes" describes behaviour that does not
  exist. It also cannot work as written, because dismissal state is initialised from
  `localStorage` before `quarterInfo` has loaded.
- **Impact:** A student who dismisses the banner once never sees a registration countdown
  again, permanently losing the feature most likely to bring them back at pass time.
- **Suggested fix:** Compare the stored quarter code against the loaded one inside an effect
  or a `useMemo` that depends on `quarterInfo`, and treat a mismatch as not dismissed.

#### UX-5: Score is called "Prof Score", "Gaucho Score" and `gaucho_score`

- **Where:** `frontend/src/pages/HomePage.tsx:97, 106, 63`; `api/schemas.py:22`; `etl/scoring.py:30`
- **What:** The homepage headlines "How Prof Score Works" and "ranked by Prof Score"; the API
  field, the database table (`gaucho_scores`), the scoring function
  (`compute_gaucho_score`), the repository name and the product documentation all say Gaucho
  Score / Gaucho Value Score. The course page itself labels the control "Customize Ranking"
  and never names the score at all — the number appears as a bare coloured badge.
- **Impact:** Users cannot connect the explanation they read on the homepage to the unlabeled
  badge on the results page, which weakens the one differentiating concept the product has.
- **Suggested fix:** Pick one name, use it in the badge's accessible label and tooltip, and
  link the badge to the methodology page proposed in UX-4.

#### UX-6: Stray "Courses" heading renders under the empty state

- **Where:** `frontend/src/components/CourseSearch.tsx:38-52`
- **What:** `CommandGroup heading="Courses"` is rendered unconditionally whenever the query is
  at least two characters, so with zero results the "No courses found" message is followed by
  an empty "Courses" group heading. Visible in
  `coursepick-search-cs16-no-results-during-500.png`.
- **Impact:** Looks like a rendering bug and suggests results failed to load below the fold.
- **Suggested fix:** Render the group only when `courses?.length` is greater than zero.

#### A11Y-2: Nested interactive elements: button inside link

- **Where:** `frontend/src/pages/HomePage.tsx:230-237`
- **What:** The call-to-action wraps a `<Button>` inside a react-router `<Link>`, producing a
  `button` nested in an `a`. The accessibility snapshot shows both as separate interactive
  nodes (`link "Start Searching"` and `button "Start Searching"`), so the same action is
  announced and tabbed to twice.
- **Impact:** Duplicate tab stops and a confusing double announcement for screen reader and
  keyboard users; invalid HTML nesting with browser-dependent activation behaviour.
- **Suggested fix:** Use the existing `asChild` pattern — `<Button asChild><Link
  to="/search">Start Searching</Link></Button>` — as `ProfessorCard` already does for
  collapsible triggers.

## Improvement backlog (pick list)

Sorted by severity, then effort.

- [x] BUG-1 — Make monitoring hit a DB-checking readiness endpoint; diagnose the live 500s (Critical, S)
- [x] BUG-2 — Strip whitespace from search queries to match ingest normalization (Critical, S)
- [x] DATA-1 — Stop publishing sub-85% name matches, or surface confidence in the UI (Critical, M)
- [x] BUG-3 — Sort grade history chronologically, not alphabetically by quarter (High, S)
- [x] BUG-4 — Fix the unreachable tag threshold so professor tags appear (High, S)
- [x] BUG-6 — Attach CORS headers to 500 responses so the SPA can see errors (High, S)
- [x] UX-1 — Distinguish API failure from "no results" in course search (High, S)
- [ ] SEC-1 — Purge the 13 MB scraped-comment dump from public git history (High, S)
- [x] BUG-5 — Apply the Bayesian adjustment in the API and unify scoring paths (High, M)
- [ ] BUG-7 — Backfill course titles from the UCSB API (High, M)
- [ ] DATA-2 — Handle truncated Nexus names; stop scoring unmatched professors as neutral (High, L)
- [x] BUG-9 — Require a department match for initial-only links (Medium, S)
- [x] BUG-11 — Replace falsy-zero guards with `is not None` in scoring (Medium, S)
- [x] BUG-12 — Implement or remove `normalize_gpa`'s unused `dept_median` (Medium, S)
- [x] BUG-13 — Fix the UCSB API key so `/quarters/current` stops 502ing (Medium, S)
- [x] ARCH-1 — Add the missing `scheduled_sections` migration plus its indexes (Medium, S)
- [x] ARCH-3 — Extract one timezone-aware quarter helper; delete the three copies (Medium, S)
- [x] PERF-1 — Split requirements so the API host stops installing Streamlit and Plotly (Medium, S)
- [x] UX-2 — Stop blaming the user's connection; add a retry button (Medium, S)
- [x] UX-3 — Correct the sentiment factor explanation on the homepage (Medium, S)
- [ ] UX-4 — Add source attribution and data-freshness timestamps (Medium, S)
- [x] A11Y-1 — Give the GPA trend chart a role, label, and table alternative (Medium, S)
- [x] SEO-1 — Add a canonical URL and de-index the vercel.app domain (Medium, S)
- [x] TEST-2 — Run frontend tests, lint and typecheck in CI; gate deploys on it (Medium, S)
- [ ] SEC-2 — Rate-limit the public search and professors endpoints (Medium, M)
- [x] BUG-8 — Prune consumed RMP candidates in matcher passes 1 and 3 (Medium, M)
- [x] BUG-10 — Refuse to merge ambiguous abbreviated-name duplicates (Medium, M)
- [ ] ARCH-2 — Move `queries.py` out of `dashboard/`; delete the Streamlit app (Medium, M)
- [ ] PERF-2 — Paginate the professors endpoint and defer heavy per-professor fields (Medium, M)
- [x] SEO-2 — Add robots.txt/sitemap and per-route meta for deep links (Medium, M)
- [x] TEST-1 — Add contract tests for ordering, tags, search, and scoring parity (Medium, M)
- [x] BUG-14 — Make banner dismissal actually expire on quarter change (Low, S)
- [x] UX-5 — Settle on one name for the score and label the badge (Low, S)
- [x] UX-6 — Hide the "Courses" group heading when there are no results (Low, S)
- [x] A11Y-2 — Un-nest the button inside the homepage CTA link (Low, S)

## Explicitly checked and found OK

Verified during this audit; future audits can skip these unless the code changes.

- **Connection pooling** — `db/connection.py:20-26` sets `pool_size=5`, `max_overflow=10`,
  `pool_recycle=1800`, `pool_pre_ping=True` behind a double-checked lock, with a correct note
  about `threading.Lock` not being re-entrant. The March CONCERNS entry is resolved.
- **N+1 in professor listings** — `get_professors_for_course` is now three queries total with
  subqueries for latest rating, sentiment average and recent-quarter counts. The March
  concern is resolved.
- **Request-scoped sessions** — `api/dependencies.py:6-18` yields one session per request and
  closes it in a `finally`, reusing the shared factory rather than creating engines.
- **Hardcoded RMP auth token** — `scrapers/rmp_scraper.py:110` now reads
  `os.environ["RMP_AUTH_TOKEN"]` and fails loudly if absent. The dummy `dGVzdDp0ZXN0` default
  flagged in March is gone, and the token is not logged.
- **SQL injection and ILIKE wildcard abuse** — all queries use SQLAlchemy ORM constructs; no
  raw SQL string interpolation anywhere in `api/` or `dashboard/queries.py`. The search
  endpoint's `pattern=r"^[a-zA-Z0-9 \-]+$"` rejects `%` and `_` with 422 (verified live), so
  wildcard-based DoS is blocked.
- **Foreign-key indexes** — `1fd97b94581d_add_fk_indexes.py` covers `grade_distributions`,
  `rmp_ratings`, `rmp_comments` and `gaucho_scores` FKs with `if_not_exists`. Complete for the
  tables it knows about; `scheduled_sections` is the gap (ARCH-1).
- **Per-comment tag deduplication** — the logic in `dashboard/queries.py:243-263` correctly
  gives each comment one vote per tag, with a clear docstring explaining the invariant. The
  algorithm is right; only the unreachable threshold (BUG-4) is wrong.
- **Route declaration order** — `/courses/search` is declared before `/courses/{course_id}`
  with an explanatory comment, avoiding the 422 that the reverse order would cause.
- **SPA deep linking** — direct navigation to `/courses/14397` loads correctly via the
  `vercel.json` rewrite; no 404. Apex-to-www redirect works (307).
- **Mobile layout at 375px** — verified by emulation. Text wraps cleanly, the score-breakdown
  bar and its labels fit without overflow, the hamburger menu appears, and tap targets use
  `min-h-[44px]`. No horizontal scrolling or overlap found.
  Screenshot: `coursepick-home-mobile-375.png`.
- **Heading structure and landmarks** — one `<h1>` per page, logical `h2`/`h3` nesting, a
  working "Skip to content" link, `<main id="main-content">`, and a labeled
  `<nav aria-label="Breadcrumb">`. Confirmed via accessibility snapshot.
- **Form and control accessibility** — the search input is an accessible `combobox` named
  "Search courses"; weight toggles expose `checkbox` roles with names ("Easy Grades", "Great
  Teaching", "Low Difficulty", "Good Reviews") and correct checked states; quarter filter
  buttons use `aria-pressed`. Collapsible triggers have explicit `aria-label`s.
- **Weight toggle guard** — `WeightToggles.tsx:25-29` prevents unchecking the last enabled
  factor (with a shake animation), so `normalizeToggles` can never divide by zero and the
  score cannot silently become meaningless.
- **Cold-start messaging** — `useColdStartMessage` shows an explanatory banner after 3
  seconds of loading, and `CoursePage` renders skeleton cards meanwhile. Good handling of the
  Render free-tier constraint.
- **Client-side re-ranking performance** — ranking is wrapped in a `useMemo` keyed on
  professors, weights and both filters, so toggling weights recomputes without refetching.
  The "real-time" claim holds.
- **Nightly sync error handling** — `scheduler/jobs.py:98-124` catches per-department failures,
  rolls back, continues, and then raises at the end so the GitHub Actions run goes red rather
  than exiting 0. The March "broad except" concern is addressed here specifically.
- **Weekly backup workflow** — `weekly-pgdump.yml` correctly installs the PostgreSQL 17 client
  from PGDG and puts it first on PATH, with comments explaining the Neon version mismatch and
  Debian `pg_wrapper` behaviour.
- **Committed secrets** — `.env.example` contains only placeholders; no `.env` is tracked; the
  committed dump contains no credentials (grepped for connection strings and passwords).
  `docker-compose.yml` uses throwaway local `gco/gco` credentials, which is fine for local dev.

---

*Audit performed 2026-09-19. Live observations against https://www.coursepick.app and
https://gaucho-course-optimizer.onrender.com between 16:45 and 17:30 PT.*

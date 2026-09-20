# Spec: Continue the 2026-09-19 Audit Remediation

You are continuing an in-progress remediation of findings from a critical audit of the
**Gaucho Course Optimizer** — a dashboard where UCSB students search courses and see
professors ranked by a "Gaucho Score" combining grade distributions (Nexus data) with
RateMyProfessors ratings and comment sentiment.

Read `docs/audits/2026-09-19-critical-audit.md` first. It contains every finding with
`file:line` evidence, live reproduction steps, impact analysis, and suggested fixes. This
spec tells you which findings are already fixed, which to do next and in what order, and
the project conventions you must follow. Where this spec and the audit doc disagree on
detail, trust the code as it exists now — several files have changed since the audit.

---

## 1. System overview

| Layer | Tech | Location | Deployed to |
|---|---|---|---|
| Frontend SPA | React 18 + Vite + TS + Tailwind v4 + TanStack Query | `frontend/` | Vercel → https://www.coursepick.app |
| API | FastAPI + SQLAlchemy | `api/` | Render → https://gaucho-course-optimizer.onrender.com |
| Query layer | shared by API and legacy app | `dashboard/queries.py` | (imported by API) |
| ETL / matching | fuzzy name matching, scoring, VADER NLP | `etl/`, `scrapers/` | run via GitHub Actions / manually |
| DB | Postgres on Neon (Launch plan) | `db/models.py`, Alembic in `db/migrations/` | Neon us-west-2 |
| Legacy UI | Streamlit (dead code, but `queries.py` lives in its package) | `dashboard/app.py` | not deployed |

Key data flow: `scrapers/grades_ingester.py` loads Nexus grade distributions;
`scrapers/targeted_scrape.py` + `etl/enhanced_matcher.py` link Nexus professors to RMP
profiles with a `match_confidence` (0–100) on the `professors` row;
`dashboard/queries.py:get_professors_for_course` assembles the data;
`api/routers/courses.py:get_professors` computes factors and Gaucho Scores per request;
the frontend re-derives scores client-side in `frontend/src/lib/scoring.ts` using the
factor values the API returns.

## 2. Already fixed — do not redo (commits `c8d96e8`..`e4612a2`, all pushed)

- **BUG-1** `/ready` endpoint (SELECT 1, 503 on failure) exists in `api/routers/health.py`.
  The outage root cause was a Neon free-tier quota; the project is now on the Launch plan.
- **BUG-2** search whitespace normalization — `dashboard/queries.py:search_courses`.
- **BUG-3** chronological grade history — `get_grade_history` sorts by `(year, QUARTER_ORDER)`.
- **BUG-4** tags fixed: keywords stored per comment (`etl/nlp_processor.py`), backfill exists.
- **BUG-5** Bayesian small-sample adjustment now applied in `api/routers/courses.py`.
- **BUG-6** JSON 500s with CORS headers + correlation id (`api/main.py`).
- **BUG-9** pass 1 initial-only links now require a department match (`etl/enhanced_matcher.py`).
- **UX-1** `CourseSearch.tsx` distinguishes API failure from empty results.
- **DATA-1** write threshold raised to 85 (`scrapers/targeted_scrape.py`); serve-time gate in
  `dashboard/queries.py` (`is_confident_match` from `etl/name_matcher.py`) strips RMP fields,
  tags, comments, and the RMP display name when `match_confidence` is `< 85` or `NULL`.
- **TEST-2 (partial)** CI now runs frontend lint/typecheck/tests (`.github/workflows/`).

All verified live in production after deploy. The test suite is green: **232 passed**.

## 3. Your task list, in order

Work through these one at a time. Each item: implement, test, commit, push, verify live
(push to `master` auto-deploys the API on Render and the frontend on Vercel).

### Tier 1 — data correctness (backend)

1. **BUG-11 — falsy-zero guards in scoring** (`etl/scoring.py:129-131`,
   `dashboard/queries.py` around the `mean_gpa` rounding). Replace truthiness checks with
   `is not None` for every nullable numeric factor. `api/routers/courses.py` already does
   this correctly — make the other call sites match it. Add a test where `avg_gpa=0.0` and
   `quality=0.0` flow through and are NOT replaced by the 0.5 neutral fallback.
   Careful: `rmp_num_ratings` in the Bayesian branch of `api/routers/courses.py`
   intentionally uses truthiness (0 ratings must skip the adjustment) — leave that.

2. **BUG-8 — matcher passes reuse consumed RMP candidates** (`etl/enhanced_matcher.py`).
   Pass 2 prunes linked candidates (`rmp_profs.remove(best_rmp)`); passes 1 and 3 never
   prune their `rmp_by_last` index even though `_link_professor` deletes the consumed
   RMP-only row. Track consumed RMP professor ids in a set shared across passes and filter
   candidates against it. Add an end-to-end test that runs all four passes over a fixture
   with two abbreviated Nexus rows sharing a surname/initial, asserting the second one is
   not handed a deleted candidate.

3. **BUG-10 — ambiguous dedup merges** (`etl/enhanced_matcher.py` pass 4,
   `etl/name_utils.py:find_duplicate_pairs`). When one abbreviated name ("SMITH J") pairs
   with multiple full names ("SMITH JOHN", "SMITH JANE") in the same department, pass 4
   currently merges into whichever it iterates first. Group pairs by abbreviated professor
   id; merge only when exactly one full-name candidate exists; log and skip otherwise.
   Test: three professors as above → no merge, a `skipped_ambiguous` stat increments.

4. **BUG-12 — `normalize_gpa` dead parameter** (`etl/scoring.py:1-6`). Decide: implement
   department-median centering or delete the parameter. Recommended: **delete the
   parameter** and fix the docstring (simplest honest fix; the API never passes it and the
   only caller that does is the dead Streamlit app). Update `dashboard/app.py` callers if
   you touch their signature, or leave dead code alone if you do ARCH-2 later.

### Tier 2 — production behavior

5. **BUG-13 — `/quarters/current` 502** (`api/routers/quarters.py`, `ucsb_api/client.py`).
   Reproduce first: `curl https://gaucho-course-optimizer.onrender.com/quarters/current`.
   The UCSB API key exists as a GitHub secret (`UCSB_API_KEY`) and the nightly sync works,
   so the key is likely valid but missing/wrong **in Render's environment**, or the router
   sends it differently than the sync does. Compare header construction between the working
   sync path and the failing router path. Log the upstream status code instead of
   collapsing everything into one 502 string. Consider caching the last good quarter
   response with a long TTL since quarter boundaries change four times a year. Note: you
   cannot change Render env vars yourself — if that turns out to be the fix, say so
   explicitly in your summary so the maintainer can update the dashboard.

6. **BUG-14 — registration banner dismissal never expires**
   (`frontend/src/components/RegistrationBanner.tsx`). Key the localStorage dismissal by
   quarter code (e.g. `banner-dismissed-20264`) so a new quarter re-shows the banner.

7. **UX-2 — error state blames the user** (`frontend/src/pages/CoursePage.tsx`). Replace
   "check your internet connection" copy with a server-fault message and add a retry
   button wired to TanStack Query's `refetch`.

8. **UX-3 — sentiment factor explained incorrectly** (`frontend/src/pages/HomePage.tsx`).
   The copy claims sentiment comes from RMP's rating; it is actually VADER compound scores
   over comment text, mapped from [-1,1] to [0,1]. Fix the copy.

9. **UX-5 / UX-6 — naming and empty-state polish** (frontend). Pick one user-facing name
   for the score ("Gaucho Score") and use it everywhere; hide the "Courses" group heading
   when there are zero results.

### Tier 3 — architecture and hygiene

10. **ARCH-3 — quarter-code derivation duplicated three times, timezone-naive**
    (`api/routers/courses.py:61-73` and two other sites — grep for `2026` patterns /
    month-based quarter branching). Extract one helper (suggest `ucsb_api/quarters.py`)
    that uses `America/Los_Angeles` dates, and call it from all three sites. Unit-test the
    quarter boundaries (Mar/Apr, Jun/Jul, Aug/Sep, Dec/Jan).

11. **ARCH-1 — missing Alembic migration for `scheduled_sections`** (`db/migrations/`).
    Generate a migration matching the model in `db/models.py` (the table already exists in
    prod, so the migration must be written to be a no-op when the table exists —
    use `IF NOT EXISTS` semantics or check inspector state). Include its indexes.

12. **PERF-1 — split requirements** (`requirements.txt`). Create `requirements-api.txt`
    with only what `api/`, `dashboard/queries.py`, `etl/scoring.py`, `etl/name_matcher.py`,
    `db/` and `ucsb_api/` import at runtime. Point the Render build at it (`render.yaml` if
    present, otherwise note the dashboard change needed). Keep the full `requirements.txt`
    for ETL/CI. Verify no API-imported module is dropped: run the API tests against a venv
    built from the new file.

13. **A11Y-1 / A11Y-2** — give `GpaTrendChart` an accessible `role="img"` +
    `aria-label` summarizing the trend; un-nest the button inside the homepage CTA link.

14. **SEO-1 / SEO-2** — add `link rel=canonical` for coursepick.app, fix the
    `vercel.json` rewrites so `/robots.txt` and `/sitemap.xml` are served (they currently
    rewrite to the SPA), add both files, and set per-route titles (react-helmet or manual
    `document.title` in route components).

15. **TEST-1** — add contract tests still missing after tonight's work: API scoring parity
    with `frontend/src/lib/scoring.ts` (same factors in → same score out, within rounding),
    and a test pinning the professors-response JSON shape.

### Explicitly out of scope — do NOT do these

- **SEC-1 (git history purge of `data/gco_dump.sql`)** — destructive history rewrite;
  requires the maintainer to run it and coordinate force-push. Skip it; flag it in your
  summary as still open.
- **DATA-2 (truncated Nexus names, Large effort)** — needs a design discussion first.
- **ARCH-2 (delete Streamlit / move queries.py)** — large mechanical move; do it only if
  everything above is done, as its import churn will conflict with other edits.
- **SEC-2 (rate limiting)** — needs a decision on Redis vs in-memory on Render's free tier.
- Do not modify `.github/workflows/weekly-pgdump.yml` or the Neon/Render/Vercel dashboards.
- Do not run the scrapers against live RMP or the UCSB API.

## 4. Project conventions (follow exactly)

### Environment & tests

```bash
# Python venv already exists at .venv (Python 3.12). If missing:
python3.12 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt

# Tests need Postgres. Port 5432 is OCCUPIED by an unrelated project — use 5433.
# A container named gco-test-pg may already exist:
docker start gco-test-pg || docker run --rm -d --name gco-test-pg -p 5433:5432 \
  -e POSTGRES_USER=gco -e POSTGRES_PASSWORD=gco -e POSTGRES_DB=gco_test postgres:16

# Run the suite (232 tests currently green):
DATABASE_URL="postgresql://gco:gco@localhost:5433/gco_test" .venv/bin/python -m pytest tests/ -q

# Frontend:
cd frontend && npm test -- --run && npm run lint && npx tsc --noEmit
```

Test fixtures note: `get_professors_for_course` only returns RMP fields when the seeded
`Professor` has `match_confidence >= 85`. Any new fixture that expects RMP data in results
must set e.g. `match_confidence=95`.

### Commits & deploy

- One commit per finding (or per tightly-coupled pair), conventional-commit style:
  `fix(scoring): treat 0.0 ratings as data, not missing (BUG-11)`. Body explains the user
  impact, not just the mechanics.
- Author identity: `git -c user.name="Hratchg" -c user.email="hratchghanime@gmail.com" commit ...`
- Push to `master`. Render redeploys the API in ~3–5 minutes; Vercel redeploys the frontend
  in ~1–2. CI (`Tests` workflow) runs Python + frontend checks on push.
- **Verify live after each backend deploy**: poll
  `https://gaucho-course-optimizer.onrender.com/ready` for 200, then spot-check the changed
  behavior (e.g. for BUG-13, `/quarters/current` should stop 502ing). Course id `14397`
  (MATH4A) is a good probe: `/courses/14397/professors`.

### Guardrails

- Never lower the 85% confidence gate or bypass `is_confident_match`.
- Never commit `.env`, dumps, or anything under `data/`.
- If a fix requires a production env-var or dashboard change you cannot make, implement the
  code side, and list the manual step prominently in your final summary.
- The matcher and dedup code mutate/delete rows — every change there needs a test proving
  the destructive path is guarded before you commit.
- Keep the audit doc untouched; it is the historical record. Track your progress by
  checking items off in the "Improvement backlog" checklist at the bottom of it — that's
  the one exception to the previous sentence.

## 5. Definition of done

- Tiers 1 and 2 complete: fixes committed, pushed, CI green, verified live.
- Tier 3 attempted in order as time allows; skipped items listed with reasons.
- Full Python suite and frontend checks pass locally before every push.
- Final summary lists: each finding fixed (with commit hash), live verification evidence,
  manual steps the maintainer must still take (Render env vars, SEC-1 history purge,
  UptimeRobot monitor pointing at `/ready` if not yet done).

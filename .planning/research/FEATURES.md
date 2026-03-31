# Feature Landscape

**Domain:** Professor/course ranking web app for college students (UCSB-specific)
**Researched:** 2026-03-30
**Confidence:** HIGH (core features), MEDIUM (competitive gaps), LOW (v2 speculation)

---

## Competitive Landscape

Before categorizing features, here is the relevant competition:

| Tool | What It Does | Key Gap |
|------|-------------|---------|
| **Rate My Professors (RMP)** | Subjective professor reviews, quality/difficulty/tags, ~1.7M professors | No grade data, no UCSB-specific optimization, review quality varies, heavily ad-laden, reviews deletable by professor request |
| **UCSBPlat** | UCSB course/professor search, star ratings, GE finder, schedule builder, grading trends | Not centered on Gaucho Score; no customizable weighting; grade data and RMP data shown separately rather than fused into one score |
| **GauchoClass (Devpost)** | AI chatbot combining UCSB data + RMP + grade distributions | Chat interface creates friction for quick lookup; no persistent ranked list to scan before GOLD registration |
| **PolyRatings (Cal Poly)** | School-specific professor ratings, ML review moderation, open source | Cal Poly only, no grade distribution integration |
| **GradeToday** | Grade distributions by course/professor | No RMP integration, no composite score |

**Conclusion:** No existing tool fuses grade distributions + RMP data + NLP sentiment into a single ranked, customizable score for UCSB. That is the core differentiator. The goal is not to replace RMP — it is to be the decision layer on top of all data sources.

---

## Table Stakes

Features where absence causes students to leave immediately or distrust the tool. These are the non-negotiables.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Course search with autocomplete** | Every modern search tool has this. Typing a full course code and pressing enter is friction. UCSBPlat, GOLD, and most tools do this. | Low | Autocomplete fires after 1–2 characters. Returns course names and codes. Keyboard navigable. |
| **Professor ranking list per course** | Core promise of the tool. User selects a course; sees all professors who have taught it, ranked. Without this it is not a ranking tool. | Low | Ordered by Gaucho Score descending by default. Show score prominently. |
| **Gaucho Score displayed per professor** | Students need a single number to compare professors at a glance. The whole backend exists for this. | Low | Show 0–100 with a visual indicator (color band or bar). |
| **Grade distribution chart** | Every UCSB-specific competitor (UCSBPlat, GauchoClass) shows this. Students directly use it to gauge GPA risk. Absence would be noticed immediately. | Medium | Bar chart: % of students per letter grade (A+/A/A-/B+...F). Per professor per course. Use Recharts or similar. |
| **GPA trend over time** | Students want to know if a professor has gotten harder/easier. One chart isn't enough. | Medium | Line chart: average GPA by quarter. Shows trajectory, not just snapshot. |
| **RMP data display** | Students already go to RMP for this. Showing it alongside grade data saves them a tab. Quality, difficulty, "would take again" %. | Low | Pull from existing `RmpRating` model. No need to replicate RMP's review submission. |
| **Recent RMP comments** | Students read comments more than scores. Sentiment-tagged comments are higher value than raw comments. | Low | Show 3–5 most recent with VADER sentiment badge (positive/neutral/negative). Already computed in pipeline. |
| **Mobile-responsive layout** | GOLD is used on mobile during orientation and pass times. Students check professor info on their phones. Not a mobile app — responsive web. | Medium | Cards stack vertically on mobile. Charts must render correctly on small screens. Search must be thumb-accessible. |
| **Loading states and error states** | Students lose trust in blank screens or silent failures. Render free tier has cold starts. | Low | Skeleton loaders for professor cards. Explicit "no results" state for search. |

---

## Differentiators

Features that make the Gaucho Course Optimizer meaningfully better than anything currently available to UCSB students. These are the competitive moat.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Real-time weight sliders (Gaucho Score formula)** | No competitor lets students customize the ranking formula. A student who cares only about GPA and ignores RMP difficulty can reflect that. The Streamlit prototype already validates this is useful. | Medium | Four sliders: GPA weight, RMP quality weight, difficulty weight (inverse), sentiment weight. Scores recompute in browser without an API call — weights are applied to pre-fetched normalized values. |
| **Bayesian-adjusted scores** | Raw averages mislead when sample sizes are small. A professor with 2 reviews at 5.0 should not outrank one with 50 reviews at 4.8. The pipeline already implements this. | None (existing) | Surface this to users as a "confidence" label or tooltip: "Score adjusted for sample size." Builds trust in the number. |
| **Sentiment-enriched comments** | RMP shows raw comments. The pipeline uses VADER sentiment + TF-IDF keywords per professor. This surfaces signal (e.g., "exams are fair", "lectures are fast-paced") faster than reading 30 comments. | Low | Show top extracted keywords as tags on each professor card. Sentiment badge on each comment. Already computed. |
| **UCSB-specific branding and context** | "Gaucho Score" resonates with UCSB students. Generic tools feel foreign. School-specific tools (PolyRatings for Cal Poly) have higher trust and adoption among that school's students. | None | Use UCSB color palette (navy/gold), use "Gaucho" terminology throughout. |
| **Combined data fusion** | RMP shows opinions. Daily Nexus shows grades. No tool at UCSB shows both side-by-side for the same professor in the same course. The matching pipeline exists to enable this. | None (existing) | Side-by-side layout: grade distribution on left, RMP data on right, Gaucho Score as the synthesis at the top. |
| **Professor comparison across sections** | When a course has 3 sections with different professors, students need to compare them directly. A ranked list is step one; visual side-by-side comparison is step two. | Medium | Stretch feature: "Compare" checkbox on two or three professor cards opens a comparison view. Defer to v1.1 if time-constrained. |
| **Quarter-by-quarter grade filtering** | A professor may have gotten harder (or easier) after returning from sabbatical. Showing grade distributions filtered to recent quarters is more actionable than all-time averages. | Medium | Dropdown to filter chart to "Last 4 quarters", "Last 2 years", "All time". Sends filter param to API. |
| **Data freshness indicator** | Students want to know if data is current. RMP doesn't show when reviews were scraped. Showing "Updated 2 days ago" builds trust and explains why scores may differ from what students see on RMP directly. | Low | Show last pipeline run timestamp. Surface in footer or tooltip. |

---

## Anti-Features

Features to deliberately not build in v1. Each has a reason grounded in scope, trust, or complexity.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **User accounts / saved favorites** | Adds auth complexity (JWT, session management, email verification). Out of scope per PROJECT.md. Adds liability for storing student data. Almost no benefit for a tool used 2–3 times per quarter during registration. | Stateless public tool. No login. No saved state. If persistence is wanted later, use localStorage for recently viewed courses (no backend). |
| **Allowing students to submit reviews** | Requires moderation, spam prevention, rate limiting, and legal review for a student project. RMP already collects reviews — duplicating that effort with worse moderation creates noise. | Link out to RMP for review submission. Display existing RMP data. Do not become a review platform. |
| **AI chatbot / natural language query** | GauchoClass already does this. It adds LLM API costs, latency, and hallucination risk. The target user (student checking professors before GOLD registration) wants a ranked list, not a conversation. | Structured search and ranked list is faster and more reliable for the actual use case. |
| **Course schedule builder / calendar view** | UCSBPlat already does this. It is a separate product with substantial scope (GOLD API integration, section management, conflict detection). | Deep-link to GOLD or UCSBPlat for schedule building. Stay focused on the ranking/data layer. |
| **Professor photos or social profiles** | Adds no decision-making value. Photos create privacy concerns (misuse, identity confusion across professors with the same name). UCSBPlat shows photos; it is not a differentiator. | Display professor name and department. No photos. |
| **Department-level or school-level rankings** | "Best CS department" or "easiest major" is a different product with different data needs. It dilutes the focused value proposition. | Keep scope to course-level professor ranking. |
| **Notifications / email alerts for grade updates** | Requires email infrastructure and user data storage. Out of scope for free-tier deployment. | Data updates silently via APScheduler. Users see fresh data on next visit. |
| **Admin dashboard for managing pipeline** | Out of scope per PROJECT.md. Adds authentication surface area. Pipeline management should stay CLI-based. | Use existing `scripts/run_pipeline.py` CLI for pipeline operations. |
| **"Rate this tool" feedback widget** | Adds noise; feedback from a small UCSB audience is low signal for a student project. | If feedback is wanted, a simple Google Form link in the footer is sufficient. |

---

## Feature Dependencies

The following dependencies are hard constraints — a feature cannot ship without its prerequisite:

```
Course search (autocomplete) → FastAPI /search/courses endpoint
    ↓
Professor ranking list → FastAPI /courses/{id}/professors endpoint
    ↓
Gaucho Score display → Score in API response (computed during pipeline)
    ↓
Grade distribution chart → GradeDistribution records in DB (per professor, per course)
    ↓
GPA trend chart → Same GradeDistribution records, grouped by quarter

RMP data display → RmpRating matched via enhanced_matcher.py
    ↓
Recent comments with sentiment → RmpComment records + VADER scores from nlp_processor.py
    ↓
Keyword tags → TF-IDF keywords in Professor.keywords JSON field

Weight sliders (real-time re-ranking) → Normalized factor scores in API response
    (sliders apply weights in browser — no additional API call needed if raw factors returned)

Quarter filter on grade chart → API accepts ?since_quarter=YYYY-QQ param
    (minor extension to existing query, deferred to v1.1)
```

---

## MVP Recommendation

The Streamlit prototype already validates what students find useful. The MVP React app should replicate that prototype faithfully before adding anything new.

**Prioritize (ship in v1):**

1. Course search with autocomplete (table stakes, blocks everything else)
2. Professor ranking list with Gaucho Score (core promise)
3. Grade distribution bar chart (most-checked data for UCSB students)
4. RMP quality/difficulty display with recent sentiment-tagged comments (table stakes)
5. Real-time weight sliders (already validated in prototype, medium complexity, clear differentiator)
6. GPA trend chart (already in Streamlit prototype, medium complexity)
7. Keyword tags on professor card (low complexity, uses existing pipeline output)
8. Mobile-responsive layout (required for pass-time phone use)

**Defer to v1.1:**

- Quarter-by-quarter grade filtering: useful but adds API complexity; all-time data is sufficient for launch
- Professor comparison view: valuable but scope risk; the ranked list alone answers the core question
- Data freshness timestamp: low complexity but polish-level; add after core features stabilize

**Defer indefinitely:**

Everything in the anti-features table above.

---

## Mobile UX Notes

UCSB students use phones during GOLD pass times (often 7 AM on a weekday). The following mobile-specific constraints apply:

- Search bar must be the first interactive element, large touch target, prominent on load
- Professor cards must be full-width on mobile and scannable without horizontal scrolling
- Charts (Recharts) must be responsive containers — `width="100%"` with `aspect` ratio, not fixed px width
- Weight sliders must have large enough touch targets (min 44px height per iOS HIG)
- The ranked list must load fast — Render free tier has cold start latency; show skeleton cards immediately
- Avoid hover-only interactions for any information that matters (tooltips that only work on desktop)

---

## Sources

- [Rate My Professors](https://www.ratemyprofessors.com/) — feature reference (quality/difficulty/tags/comments model)
- [Rate My Professors Wikipedia](https://en.wikipedia.org/wiki/Rate_My_Professors) — feature history, scale, review model
- [PolyRatings](https://polyratings.dev/) — school-specific rating tool comparison (Cal Poly SLO)
- [PolyRatings GitHub](https://github.com/Polyratings/polyratings) — open source reference for architecture and features
- [UCSBPlat](https://ucsbplat.com) — direct UCSB competitor; autocomplete, grading trends, schedule builder
- [GauchoClass Devpost](https://devpost.com/software/gauchocourse) — AI-chatbot approach to same data sources
- [Coursicle — Websites Like Rate My Professor](https://www.coursicle.com/blog/websites-like-rate-my-professor/) — competitor landscape
- [Best 10 Professor Rating Sites 2025 — Wegic](https://wegic.ai/blog/best-professor-rating-sites) — competitive feature matrix
- [Search UX Best Practices 2026 — Design Monks](https://www.designmonks.co/blog/search-ux-best-practices) — autocomplete UX standards
- [Autocomplete UX — Smart Interface Design Patterns](https://smart-interface-design-patterns.com/articles/autocomplete-ux/) — 65% higher search engagement with autocomplete
- [UCSB History Department Registration Tips](https://www.history.ucsb.edu/registration-tips-and-reminders/) — how UCSB students use professor data during registration

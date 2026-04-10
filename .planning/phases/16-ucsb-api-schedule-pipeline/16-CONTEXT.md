# Phase 16: UCSB API Client & Schedule Pipeline - Context

**Gathered:** 2026-04-10
**Status:** Ready for planning
**Mode:** Auto-generated (backend infrastructure phase)

<domain>
## Phase Boundary

Build the backend integration with UCSB's Academic Curriculums API and Quarter Calendar API. Create an API client module, a new ScheduledSection database model, a name-matching function to link UCSB instructors to existing professor records, a pipeline that fetches and stores next-quarter schedule data, and a nightly APScheduler job to keep data current. Expose schedule data through the existing professors endpoint.

</domain>

<decisions>
## Implementation Decisions

### UCSB API Client
- Base URL: https://api.ucsb.edu/academics/curriculums/v3
- Quarter Calendar: https://api.ucsb.edu/academics/quartercalendar/v1
- Auth: header `ucsb-api-key` with value from env var `UCSB_API_KEY`
- API key already stored in .env: `UCSB_API_KEY=lMNGufU4pFmUBTBg6AzkQMGfsPB0fFVq`
- Rate limit: 10,000 req/min (very generous)
- Use Python `requests` library (already in deps)

### Data Model
- New table `scheduled_sections` storing:
  - professor_id (FK, nullable — null if instructor not matched)
  - course_id (FK)
  - quarter_code (text, e.g., "20262")
  - quarter_name (text, e.g., "Spring 2026")
  - enroll_code (text, UCSB enrollment code)
  - instructor_name_raw (text, e.g., "CONRAD P T" — preserve for debugging)
  - days (text, e.g., "T R")
  - begin_time (text, e.g., "14:00")
  - end_time (text, e.g., "15:15")
  - building (text)
  - room (text)
  - enrolled (int)
  - max_enroll (int)
  - fetched_at (datetime)

### Name Matching
- UCSB API returns "LASTNAME F M" format (uppercase)
- Parse: split by space → first token is last_name, remaining are initials
- Match against professors.name_rmp and professors.name_nexus:
  - Exact last name match (case-insensitive) + first initial match
  - Fall back to fuzzy last name match (Levenshtein) if exact fails
- Log unmatched instructors for manual review
- Use existing `thefuzz` library (already in deps)

### Schedule Pipeline
- Fetch all sections for a given quarter + course from UCSB API
- Parse instructor names, match to professors, store sections
- Called per-course when professors endpoint is hit (lazy fetch with TTL cache)
- OR bulk fetch for popular departments via nightly APScheduler job
- Nightly job: fetch next quarter's schedule for all departments with existing course data

### API Changes
- Add `scheduled_sections` field to professors endpoint response
- Each section: {quarter, days, time, building, room, enrolled, max_enroll}
- Add `teaching_next_quarter` boolean derived from scheduled_sections

### Claude's Discretion
- Exact file structure for UCSB API client module
- Cache TTL for schedule data (suggest 4-6 hours)
- Whether to add a new router or extend existing courses router
- Error handling for UCSB API downtime
- Pagination handling for large department queries

</decisions>

<code_context>
## Existing Code Insights

### Files to create
- `ucsb_api/client.py` — UCSB API client (classes search, quarter calendar)
- `ucsb_api/name_matcher.py` — instructor name parsing and matching
- `ucsb_api/schedule_sync.py` — pipeline to fetch, match, and store sections
- `db/models.py` — add ScheduledSection model
- `tests/test_ucsb_api.py` — client + matcher tests

### Files to modify
- `api/config.py` — add UCSB_API_KEY setting
- `api/schemas.py` — add ScheduledSectionResponse schema
- `api/routers/courses.py` — add schedule data to professors response
- `dashboard/queries.py` — query scheduled_sections for professor matches

### Existing patterns
- APScheduler already configured for RMP scraper (nightly)
- SQLAlchemy models in db/models.py with Alembic migrations
- Pydantic schemas in api/schemas.py
- requests library already in requirements.txt

</code_context>

<specifics>
## Specific Ideas

UCSB API verified working with test calls:
- Quarter calendar: returns current quarter "Spring 2026", pass dates, finals dates
- Classes search: 47 CMPSC courses found with full section data
- Instructor format confirmed: "KHARITONOVA Y", "CONRAD P T"

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>

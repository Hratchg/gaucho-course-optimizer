---
phase: "16"
plan: "01"
title: "UCSB API Client, Schedule Pipeline & Nightly Job"
subsystem: backend
tags: [ucsb-api, schedule, name-matching, apscheduler, pipeline]
dependency_graph:
  requires: [db/models.py, api/config.py, api/schemas.py, api/routers/courses.py, dashboard/queries.py, scheduler/jobs.py]
  provides: [ucsb_api/client.py, ucsb_api/name_matcher.py, ucsb_api/schedule_sync.py, ScheduledSection model, nightly schedule job]
  affects: [professors endpoint, scheduler configuration]
tech_stack:
  added: [UCSB Academic Curriculums API v3, UCSB Quarter Calendar API v1]
  patterns: [API client with pagination, fuzzy name matching, upsert sync pipeline, APScheduler cron job]
key_files:
  created:
    - ucsb_api/__init__.py
    - ucsb_api/client.py
    - ucsb_api/name_matcher.py
    - ucsb_api/schedule_sync.py
    - tests/test_ucsb_client.py
    - tests/test_schedule_sync.py
  modified:
    - api/config.py
    - api/schemas.py
    - api/routers/courses.py
    - dashboard/queries.py
    - db/models.py
    - scheduler/jobs.py
    - tests/test_scheduler.py
    - tests/test_models.py
decisions:
  - UCSB API auth via "ucsb-api-key" header (not Authorization)
  - Instructor name parsing: split on space, first token = last name, rest = initials
  - Fuzzy matching uses thefuzz with 80% threshold + first-initial confirmation
  - Upsert by (quarter_code, enroll_code) unique constraint
  - Next quarter derived from current date month ranges
  - Nightly schedule refresh at 1:30 AM via APScheduler CronTrigger
metrics:
  duration: 14min
  completed: 2026-04-10
  tasks: 3
  files_created: 6
  files_modified: 8
  tests_added: 38
---

# Phase 16 Plan 01: UCSB API Client, Schedule Pipeline & Nightly Job Summary

UCSB API client with paginated class fetching, fuzzy instructor-to-professor name matching via thefuzz, ScheduledSection DB model with upsert sync pipeline, and nightly APScheduler refresh job -- professors endpoint now returns teaching_next_quarter and scheduled_sections

## What Was Built

### Task 1: UCSB API Client + Name Matcher (commit 8d05b05)

- **ucsb_api/client.py**: `UCSBApiClient` class with methods:
  - `fetch_classes(quarter_code, course_id)` -- paginated fetch from Academic Curriculums API
  - `fetch_department_classes(quarter_code, department)` -- bulk fetch for nightly job
  - `fetch_quarter_calendar(quarter_code)` -- quarter dates, pass times, finals
  - `fetch_current_quarter()` -- current quarter info
  - Helper functions: `get_next_quarter_code()`, `quarter_code_to_name()`
- **ucsb_api/name_matcher.py**: Parses UCSB instructor format ("CONRAD P T") and matches to professor records:
  - Exact last-name + first-initial match (confidence 1.0)
  - Fuzzy last-name match via Levenshtein (thefuzz, threshold 80%) + initial confirmation
  - Distinguishes same-last-name professors by initial (e.g., "CONRAD P" vs "CONRAD K")
  - Logs unmatched instructors for review
- **api/config.py**: Added `ucsb_api_key` setting (reads from UCSB_API_KEY env var)
- 27 tests covering client, utilities, parsing, and matching

### Task 2: Database Model + Schedule Sync Pipeline (commit 2572a00)

- **db/models.py**: `ScheduledSection` model with:
  - Foreign keys to professors (nullable) and courses
  - quarter_code, enroll_code, instructor_name_raw (preserved for debugging)
  - Time/location: days, begin_time, end_time, building, room
  - Enrollment: enrolled, max_enroll, section_cancelled
  - Unique constraint on (quarter_code, enroll_code) for safe upserts
- **ucsb_api/schedule_sync.py**: Pipeline functions:
  - `sync_course_sections()` -- fetch + parse + match + upsert for a single course
  - `sync_department_sections()` -- bulk sync for an entire department
  - `_normalize_course_id()` -- strips padded UCSB format ("CMPSC     130A" -> "CMPSC 130A")
  - `_extract_section_data()` -- extracts primary instructor and time/location from raw API data
- **api/schemas.py**: `ScheduledSectionResponse` Pydantic model
- Table created in production database via `Base.metadata.create_all`
- 8 tests covering sync pipeline, upserts, unmatched instructors

### Task 3: API Integration + Nightly Job (commit 15408fb)

- **dashboard/queries.py**: `get_scheduled_sections()` -- queries scheduled_sections grouped by professor_id
- **api/routers/courses.py**: Professors endpoint now includes `teaching_next_quarter` (boolean) and `scheduled_sections` (list) per professor
- **api/schemas.py**: `ProfessorRanking` updated with `teaching_next_quarter` and `scheduled_sections` fields
- **scheduler/jobs.py**: `nightly_schedule_refresh()` job runs at 1:30 AM, iterating all departments and syncing next-quarter schedule data
- 3 scheduler tests including the new nightly job

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated test_models.py expected table list (commit 7880790)**
- **Found during:** Task 3 verification
- **Issue:** test_all_tables_defined had a hardcoded set of 6 expected tables, missing the new scheduled_sections table
- **Fix:** Added "scheduled_sections" to the expected set and imported ScheduledSection
- **Files modified:** tests/test_models.py

## Test Results

- **test_ucsb_client.py**: 27 passed -- API client, utilities, name parsing, matching
- **test_schedule_sync.py**: 8 passed -- sync pipeline, upserts, unmatched handling
- **test_scheduler.py**: 3 passed -- all 3 scheduled jobs registered
- **test_courses_router.py**: 10 passed -- existing router tests unchanged
- **test_professors_router.py**: 7 passed -- existing router tests unchanged
- **test_models.py**: 3 passed -- model definition test updated

**Total: 58 tests, 58 passed, 0 failed**

## Verified with Real UCSB API

- Current quarter: Spring 2026 (20262)
- CMPSC 130A: 5 sections fetched, instructor format confirmed ("SINGH A K")
- Quarter calendar returns pass dates, finals dates as expected
- API key authentication working via ucsb-api-key header

## Self-Check: PASSED

- All 6 created files exist on disk
- All 8 modified files exist on disk
- All 4 commits found in git log (8d05b05, 2572a00, 15408fb, 7880790)

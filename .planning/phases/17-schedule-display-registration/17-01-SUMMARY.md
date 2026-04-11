---
phase: 17-schedule-display-registration
plan: 01
status: complete
started: 2026-04-10
completed: 2026-04-11
---

# Plan 17-01: Schedule Display & Registration Context

## What Was Built

Frontend display layer for UCSB live schedule data: "Teaching Next Quarter" badge on professor cards, expandable section details (day/time, building, seats), quarter filter, and registration countdown banner with GOLD link.

## Key Changes

- `api/routers/quarters.py` — New GET /quarters/current endpoint returning quarter name + pass dates from UCSB Quarter Calendar API
- `frontend/src/types/api.ts` — Added ScheduledSection and QuarterInfo interfaces
- `frontend/src/lib/api.ts` — Added fetchQuarterInfo()
- `frontend/src/hooks/useQuarterInfo.ts` — React Query hook for quarter info
- `frontend/src/components/ProfessorCard.tsx` — "Teaching Next Quarter" badge + expandable section details (day/time, building/room, enrolled/max)
- `frontend/src/pages/CoursePage.tsx` — Quarter filter (Next Quarter / Current / All)
- `frontend/src/components/RegistrationBanner.tsx` — Countdown banner with pass date, quarter name, GOLD link, dismissible
- `frontend/src/layouts/Layout.tsx` — Renders RegistrationBanner below navbar
- `frontend/src/test/mswHandlers.ts` — Updated with schedule + quarter mock data

## Test Results

100/100 frontend tests passing. Zero regressions.

## Requirements Completed

DISP-01, DISP-02, DISP-03, REG-01, REG-02

---
phase: 07-tutorial-landing-page
plan: 01
subsystem: frontend/pages
tags: [tutorial, landing-page, homepage, tdd, accessibility]
dependency_graph:
  requires: []
  provides: [tutorial-landing-page, score-breakdown-visual, factor-definitions, usage-guide, cta-to-search]
  affects: [frontend/src/pages/HomePage.tsx, frontend/src/pages/HomePage.test.tsx]
tech_stack:
  added: []
  patterns: [shadcn-card-grid, stacked-bar-visualization, full-bleed-section, tdd-red-green]
key_files:
  created: []
  modified:
    - frontend/src/pages/HomePage.tsx
    - frontend/src/pages/HomePage.test.tsx
decisions:
  - Used HTML entities for em-dash and en-dash to match UI-SPEC exact copy
  - Connector lines between usage guide steps placed inside li elements with negative margin for alignment
  - Score bar segments use inline oklch values for Difficulty and Sentiment to match exact CSS tokens
metrics:
  duration: 25m
  completed: "2026-04-07T23:53:00Z"
  tasks_completed: 2
  tasks_total: 2
  test_count: 13
  test_pass: 13
  total_suite_pass: 74
---

# Phase 7 Plan 01: Tutorial Landing Page Summary

Full tutorial landing page replacing placeholder HomePage with 5 sections (Hero, Score Breakdown, Factor Cards, Usage Guide, Final CTA) using TDD, exact UI-SPEC copywriting, and shadcn Card components with accessible score bar visualization.

## Task Results

| Task | Name | Type | Commit | Status |
|------|------|------|--------|--------|
| 1 | Write tests for tutorial landing page | test (TDD RED) | ecf4177 | Done |
| 2 | Implement full tutorial landing page | feat (TDD GREEN) | 051d527 | Done |

## What Was Built

### Section 1: Hero
- h1 heading "Find the Best Professor for Any UCSB Course" with font-heading bold 28px
- Subtext matching UI-SPEC copywriting contract exactly
- Centered layout, no CTA button (CTA is in Final CTA section only)

### Section 2: Score Breakdown
- h2 "How Gaucho Score Works" with explanation subtext
- Horizontal stacked bar with 4 teal-shade segments (GPA/Quality/Difficulty/Sentiment)
- Each segment has aria-label for accessibility (e.g., "GPA: 25%")
- Container div with role="img" and descriptive aria-label
- Labels row below with middle dot separators
- Example score badge "Example: a score of 78/100"

### Section 3: Factor Cards
- h2 "What Each Factor Means"
- 2x2 responsive grid (1-col mobile, 2-col sm+) using shadcn Card components
- Each card: lucide icon (24px, text-primary) + h3 title + jargon-free definition + example value
- GPA (GraduationCap), Quality (Star), Difficulty (TrendingDown), Sentiment (MessageCircle)

### Section 4: Usage Guide
- h2 "How to Use Gaucho Course Optimizer"
- Semantic ordered list with 3 steps
- Each step: numbered circle + lucide icon + title + body text
- Horizontal on md+, vertical stack on mobile
- Connector lines between steps on desktop

### Section 5: Final CTA Banner
- Full-bleed bg-primary section breaking out of max-w-4xl container
- h2 "Ready to Find Your Professor?" in primary-foreground color
- Amber accent "Start Searching" button linking to /search
- min-h-[44px] for WCAG 2.5.5 touch target compliance

## Test Coverage

13 test cases across 6 describe blocks:
- **page metadata** (1): document.title
- **Hero** (2): h1 heading, subtext content
- **Score Breakdown** (3): h2 heading, role="img" container, 4 segment aria-labels
- **Factor Cards** (3): h2 heading, 4 card titles as h3, 4 example values
- **Usage Guide** (2): h2 heading, 3 step titles
- **Final CTA** (2): h2 heading, /search link

## Verification

- All 13 HomePage tests pass
- Full suite: 74/74 tests pass (15 test files, 0 regressions)
- TypeScript: compiles cleanly (npx tsc --noEmit)
- Production build: succeeds (npm run build)

## Deviations from Plan

None -- plan executed exactly as written.

## Self-Check: PASSED

- [x] frontend/src/pages/HomePage.tsx exists (240 lines, min 120)
- [x] frontend/src/pages/HomePage.test.tsx exists (139 lines, min 60)
- [x] 07-01-SUMMARY.md exists
- [x] Commit ecf4177 exists (Task 1 - TDD RED)
- [x] Commit 051d527 exists (Task 2 - TDD GREEN)

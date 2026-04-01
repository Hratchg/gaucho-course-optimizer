# Phase 3: React Frontend - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.

**Date:** 2026-04-01
**Phase:** 03-react-frontend

---

## Areas Selected

User selected all 4 gray areas for discussion:
1. Professor card layout
2. Weight sliders placement
3. URL routing structure
4. Data fetching strategy

---

## Area 1: Professor Card Layout

**Q: What's visible by default vs. hidden behind an expand toggle?**
Options: Compact + expand / Tabs per card / Full card always visible
→ **Selected: Compact + expand**

**Q: When expanded, what opens — both sections together or separate toggles?**
Options: One toggle (both sections) / Separate toggles / You decide
→ **Selected: One toggle, both sections**

**Q: How should the Gaucho Score color band work?**
Options: Same as Streamlit (≥70 green, 50–69 yellow, <50 red) / Color score number only / You decide
→ **Selected: You decide** (Claude's discretion on visual implementation)

**Q: What info is in the collapsed card header?**
Options: Score + name + GPA + RMP + keywords / Score + name + GPA only / You decide
→ **Selected: Score + name + GPA + RMP + keywords** (full summary visible without expanding)

---

## Area 2: Weight Sliders

**Q: Where do the 4 weight sliders live on desktop?**
Options: Left sidebar (always visible) / Collapsible panel above results / Floating button → sheet
→ **Selected: Left sidebar, always visible**

**Q: On mobile, how should weight sliders appear?**
Options: Bottom sheet / Collapsible section above results / You decide
→ **Selected: You decide** (Claude picks based on shadcn/ui Sheet component)

**Q: Should current weights be shown as numbers alongside each slider?**
Options: Show numeric value / Visual only / You decide
→ **Selected: You decide** (Claude decides based on layout fit)

---

## Area 3: URL Routing

**Q: When a student selects a course, does the URL change to a shareable address?**
→ User requested clarification: "Which would be better for a production app with a decent amount of users?"

**Claude's analysis:**
Shareable URLs (/courses/:courseId) are significantly better for production:
- Shareability drives growth (students share links to specific courses)
- SEO: course-specific pages can rank on Google
- Analytics: see which courses get traffic
- Back button / browser history works correctly
- Bookmarking: users can save direct course links

**Q: Confirmed shareable URLs — which URL pattern?**
Options: /courses/:courseId / /?course=CMPSC8
→ **Selected: /courses/:courseId** (database integer ID, stable canonical URLs)

---

## Area 4: Data Fetching

**Q: How should the app manage API calls, loading state, and caching?**
Options: TanStack Query / Plain fetch + useState / SWR
→ User requested detailed pros/cons explanation

**Claude's explanation provided:**
- TanStack Query: caching, built-in states, retry, deduplication, best for 4 chained endpoints
- Plain fetch: no dependencies, more boilerplate, no caching, manual timer for cold-start
- SWR: lighter (~5KB), simpler API, good caching, less powerful for complex cases

→ **Selected: TanStack Query (react-query)**

---

## Decisions Summary

| Decision | Choice |
|----------|--------|
| Card default state | Compact — name, score, GPA, RMP, keywords visible |
| Card expand | Single toggle reveals both charts + comments |
| Score color banding | Claude's discretion (≥70/50–69/<50 thresholds) |
| Slider desktop | Left sidebar, always visible |
| Slider mobile | Claude's discretion (shadcn/ui Sheet) |
| URL routing | /courses/:courseId with React Router v6 |
| Data fetching | TanStack Query |

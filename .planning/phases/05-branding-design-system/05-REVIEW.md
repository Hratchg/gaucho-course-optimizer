---
phase: 05-branding-design-system
reviewed: 2026-04-07T14:40:00Z
depth: standard
files_reviewed: 10
files_reviewed_list:
  - frontend/index.html
  - frontend/src/components/GpaTrendChart.tsx
  - frontend/src/components/GradeChart.tsx
  - frontend/src/components/ProfessorCard.test.tsx
  - frontend/src/components/ProfessorCard.tsx
  - frontend/src/index.css
  - frontend/src/pages/CoursePage.test.tsx
  - frontend/src/pages/CoursePage.tsx
  - frontend/src/pages/SearchPage.test.tsx
  - frontend/src/pages/SearchPage.tsx
findings:
  critical: 0
  warning: 3
  info: 2
  total: 5
status: issues_found
---

# Phase 5: Code Review Report

**Reviewed:** 2026-04-07T14:40:00Z
**Depth:** standard
**Files Reviewed:** 10
**Status:** issues_found

## Summary

This review covers frontend files from the branding/design-system phase: the main HTML entry point, CSS theme configuration, chart components, page components, and their tests. The code is generally well-structured with proper TypeScript typing, good use of shadcn/ui components, and appropriate null-safety guards. No critical security issues were found.

Three warnings were identified: a potential NaN propagation from unvalidated route parameters, hardcoded chart colors that bypass the newly established design system, and an unstable list key in rendered comments. Two informational items note minor improvements for dark mode compatibility and test coverage.

## Warnings

### WR-01: Potential NaN propagation from unvalidated route parameter

**File:** `frontend/src/pages/CoursePage.tsx:21`
**Issue:** `Number(courseId)` produces `NaN` when `courseId` is `undefined` (which `useParams` can return if the route does not match). This `NaN` propagates to `useProfessors(NaN)` and through `ProfessorCard` into `useProfessorGrades(professorId, NaN)`. While both hooks guard with `> 0` checks (which happen to reject `NaN`), the protection is incidental rather than intentional. If any downstream consumer does arithmetic on `courseId` (e.g., comparison, string interpolation for a URL), NaN will silently corrupt the result.
**Fix:**
```tsx
const numericCourseId = Number(courseId)

// Add explicit guard after line 21:
if (Number.isNaN(numericCourseId) || numericCourseId <= 0) {
  return (
    <div className="mx-auto max-w-5xl px-4 py-12 text-center">
      <p className="font-semibold">Invalid course ID</p>
    </div>
  )
}
```

### WR-02: Hardcoded chart colors bypass design system theme

**File:** `frontend/src/components/GpaTrendChart.tsx:21` and `frontend/src/components/GradeChart.tsx:30`
**Issue:** The GPA trend line uses `stroke="#0D9488"` and the grade bar chart uses `fill="#0F766E"` -- both are hardcoded hex values. The CSS in `index.css` defines chart color tokens (`--chart-1` through `--chart-5`) as part of the design system, but these components do not use them. In dark mode, these teal colors will not adapt and may have poor contrast against the dark background (`oklch(0.145 0 0)`). For a branding/design-system phase, chart colors should be consistent with the token system.
**Fix:**
```tsx
// GpaTrendChart.tsx line 21 - use CSS variable via currentColor or inline
<Line type="monotone" dataKey="avg_gpa" stroke="var(--chart-1)" dot={false} />

// GradeChart.tsx line 30
<Bar dataKey="count" fill="var(--chart-1)" />
```
Alternatively, if Recharts does not resolve CSS custom properties in all environments, read the computed value:
```tsx
const chartColor = getComputedStyle(document.documentElement).getPropertyValue('--chart-1').trim()
```

### WR-03: Unstable list key using array index for comments

**File:** `frontend/src/components/ProfessorCard.tsx:52`
**Issue:** Comments are rendered with `key={i}` (array index). If the comment list is re-fetched and the order changes, or if comments are added/removed, React may incorrectly reuse DOM nodes, leading to stale content or visual glitches. The `CommentResult` type lacks a unique `id` field, but a composite key from available fields would be more stable.
**Fix:**
```tsx
{comments.map((comment, i) => (
  <div key={`${comment.created_at}-${i}`} className="border-b pb-3 last:border-b-0">
```
This is not perfect (created_at can be null), but provides better stability than index alone. A more robust fix would be to add an `id` field to the `CommentResult` API type.

## Info

### IN-01: Dark mode theme loses brand colors

**File:** `frontend/src/index.css:90-122`
**Issue:** The `.dark` theme block uses achromatic (gray) values for all tokens (chroma = 0 in every oklch value), completely stripping the teal/gold brand identity established in the light theme. For example, `--primary` in light mode is `oklch(0.5109 0.0861 186.39)` (teal) but in dark mode is `oklch(0.922 0 0)` (near-white gray). This appears to be the default shadcn dark theme rather than a branded dark variant.
**Fix:** Consider updating the dark theme to retain brand hues at adjusted lightness/chroma values, e.g.:
```css
.dark {
    --primary: oklch(0.75 0.06 186.39);
    --secondary: oklch(0.50 0.07 184.70);
    --accent: oklch(0.70 0.12 58.32);
    /* ... adjust other brand tokens similarly */
}
```

### IN-02: Test files do not assert loading or error states

**File:** `frontend/src/pages/CoursePage.test.tsx` and `frontend/src/pages/SearchPage.test.tsx`
**Issue:** Both page test files only verify `document.title` is set. They do not test loading states, error states, or the empty-results branch -- all of which are rendered in CoursePage. While minimal tests are better than none, the branch coverage for CoursePage's conditional rendering (error, loading with cold-start message, empty results, results list) is not exercised.
**Fix:** Add tests that mock the API responses to exercise each branch. For example:
```tsx
it('shows loading skeletons while fetching', () => {
  // Mock useProfessors to return isLoading: true
  renderWithProviders('123')
  expect(screen.getAllByTestId('skeleton-card')).toHaveLength(3)
})
```

---

_Reviewed: 2026-04-07T14:40:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

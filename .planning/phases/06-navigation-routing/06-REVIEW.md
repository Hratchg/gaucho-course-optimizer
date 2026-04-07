---
phase: 06-navigation-routing
reviewed: 2026-04-07T15:45:00Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - frontend/src/layouts/Layout.tsx
  - frontend/src/components/Navbar.tsx
  - frontend/src/components/Breadcrumbs.tsx
  - frontend/src/components/MobileMenu.tsx
  - frontend/src/pages/HomePage.tsx
  - frontend/src/App.tsx
  - frontend/src/pages/SearchPage.tsx
  - frontend/src/pages/CoursePage.tsx
  - frontend/src/components/CourseSearch.tsx
findings:
  critical: 0
  warning: 3
  info: 1
  total: 4
status: issues_found
---

# Phase 6: Code Review Report

**Reviewed:** 2026-04-07T15:45:00Z
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

The navigation and routing implementation is generally well-structured. The component decomposition is clean (Layout with Outlet, Navbar with responsive mobile/desktop split, Breadcrumbs derived from location). Accessibility considerations are present (aria-label on mobile menu trigger, aria-current on breadcrumbs, 44px touch targets). The routing uses nested routes under a layout correctly.

Three warnings were identified: (1) CoursePage does not validate or handle non-numeric courseId route params, leading to a silently broken state; (2) Breadcrumbs uses a non-null assertion on `item.to` that could produce a runtime error if the breadcrumb logic is modified; and (3) App.tsx has no catch-all route, so unmatched URLs render a blank page with no user feedback.

## Warnings

### WR-01: CoursePage does not validate courseId route parameter

**File:** `frontend/src/pages/CoursePage.tsx:21`
**Issue:** `Number(courseId)` converts `undefined` to `NaN` and non-numeric strings (e.g., `/courses/abc`) to `NaN`. When `NaN` is passed to `useProfessors`, the query is disabled (`NaN > 0` is `false`), so the component silently shows "No professors found" instead of an appropriate error message. This is a poor user experience -- a user navigating to an invalid course URL gets no indication that the URL is wrong.
**Fix:**
```tsx
const { courseId } = useParams<{ courseId: string }>()
const numericCourseId = Number(courseId)

if (!courseId || Number.isNaN(numericCourseId) || numericCourseId <= 0) {
  return (
    <div className="mx-auto max-w-5xl px-4 py-12 text-center">
      <p className="font-semibold">Invalid course ID</p>
      <p className="text-sm text-muted-foreground">
        The course could not be found. Please search for a valid course.
      </p>
    </div>
  )
}
```

### WR-02: Non-null assertion on breadcrumb link target

**File:** `frontend/src/components/Breadcrumbs.tsx:37`
**Issue:** The expression `item.to!` uses a TypeScript non-null assertion. The `BreadcrumbItem` interface defines `to` as optional (`to?: string`). The current logic in `buildBreadcrumbs` ensures non-last items always have a `to` value, but this invariant is not enforced by the type system. If `buildBreadcrumbs` is later modified (e.g., a new route added) and a non-last item accidentally omits `to`, the Link component will receive `undefined`, causing navigation to break.
**Fix:**
```tsx
<Link
  to={item.to ?? '/'}
  className="text-muted-foreground hover:text-foreground transition-colors"
>
  {item.label}
</Link>
```
Alternatively, split `BreadcrumbItem` into two types -- one for intermediate crumbs (with required `to`) and one for the terminal crumb (no `to`).

### WR-03: No catch-all route for unmatched URLs

**File:** `frontend/src/App.tsx:9-14`
**Issue:** The router has no wildcard (`*`) route. When a user navigates to an undefined path (e.g., `/about`, `/settings`, a mistyped URL), the page renders the Layout (navbar + breadcrumbs) with a completely blank main content area and no error feedback. This is confusing -- users have no way to know the page does not exist.
**Fix:**
```tsx
// Create a simple NotFoundPage component, then add:
<Routes>
  <Route element={<Layout />}>
    <Route path="/" element={<HomePage />} />
    <Route path="/search" element={<SearchPage />} />
    <Route path="/courses/:courseId" element={<CoursePage />} />
    <Route path="*" element={<NotFoundPage />} />
  </Route>
</Routes>
```

## Info

### IN-01: Breadcrumb regex matches any nested path under /courses/

**File:** `frontend/src/components/Breadcrumbs.tsx:65`
**Issue:** The regex `/^\/courses\/(.+)$/` uses `.+` which matches any characters including slashes. This means a path like `/courses/123/reviews` would still match and render breadcrumbs as if it were a single course page. Currently no such routes exist so this is benign, but the regex could be tightened if sub-routes are added later.
**Fix:** If only numeric IDs are expected, tighten the regex:
```ts
const courseMatch = pathname.match(/^\/courses\/(\d+)$/)
```

---

_Reviewed: 2026-04-07T15:45:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

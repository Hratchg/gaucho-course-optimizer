# Phase 11: Standardized Keywords - Context

**Gathered:** 2026-04-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace raw NLP-extracted keywords with a curated vocabulary of ~15 meaningful professor tags. Backend maps raw keywords to standardized tags with frequency counting. Frontend displays tags as pill badges with hover tooltips showing review count. Only tags mentioned in 3+ reviews appear.

</domain>

<decisions>
## Implementation Decisions

### Keyword Vocabulary & Classification
- Classification happens in the backend — add a mapping function in `dashboard/queries.py` that maps raw keywords to curated tags before returning
- ~15 curated tags covering teaching style, grading, workload, and personality
- Mapping approach: keyword-to-tag lookup dict (e.g., "easy" → "Easy Grader", "hard" → "Tough Exams", "boring" → "Dry Lectures") with simple substring/fuzzy matching
- Unmapped keywords are dropped — only curated tags are returned to the frontend
- Frequency threshold: tags must appear in 3+ reviews to be shown (noise filtering)
- API response changes: `keywords: string[]` becomes `tags: [{name: string, count: number}]` (or similar structured format with counts)

### Frontend Display
- Pill badges using shadcn Badge component — muted variant for a subtle, consistent look
- Native HTML `title` attribute on each badge for hover tooltip — simple, cross-platform
- Tooltip format: "Easy Grader — 7 reviews" matching ROADMAP success criteria
- Max 6 tags displayed, sorted by frequency (most mentioned first)
- Replace current `professor.keywords` rendering in ProfessorCard with new tag display

### Claude's Discretion
- Exact curated vocabulary list (~15 tags)
- Fuzzy matching implementation (substring match, stemming, or simple includes)
- Whether to add a new TypeScript type for tags or extend ProfessorRanking
- API response field name and structure for tags with counts
- Test approach for the mapping function

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `dashboard/queries.py` — keywords are extracted from `RmpComment.keywords` (JSON array), grouped by rating_id, deduplicated, capped at 8
- `db/models.py` — `RmpComment` model has `keywords` column (JSON array of strings)
- `api/schemas.py` — `ProfessorRanking` schema has `keywords: list[str]`
- `frontend/src/components/ProfessorCard.tsx` — displays `professor.keywords` as Badge pills
- `frontend/src/types/api.ts` — `ProfessorRanking.keywords: string[]`

### Established Patterns
- Backend: keyword extraction in `get_professors_for_course()` already collects per-rating keywords
- Frontend: Badge component from shadcn/ui already used for score display
- API contract: add/change fields in schema → update TypeScript interface → update MSW handlers

### Integration Points
- `dashboard/queries.py` — add tag mapping function, change keyword aggregation to return structured tags
- `api/schemas.py` — change `keywords` field type or add new `tags` field
- `api/routers/courses.py` — pass through updated field
- `frontend/src/types/api.ts` — update ProfessorRanking interface
- `frontend/src/components/ProfessorCard.tsx` — update tag display with tooltips
- `frontend/src/test/mswHandlers.ts` — update mock data

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond the decisions above.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

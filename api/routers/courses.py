from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.rate_limit import limiter
from api.schemas import CourseResult, ProfessorRanking, ScheduledSectionResponse
from db.queries import get_all_course_sections, get_professors_for_course, get_scheduled_sections, search_courses
from etl.scoring import (
    bayesian_adjust,
    compute_gaucho_score,
    normalize_difficulty,
    normalize_gpa,
    normalize_quality,
)
from ucsb_api.quarters import current_and_next_quarter_codes

router = APIRouter()


# IMPORTANT: /search must be declared BEFORE /{course_id}/professors.
# FastAPI matches routes in declaration order. If /{course_id} comes first,
# GET /courses/search?q=x would match with course_id="search" → 422 int parse error.


@router.get("/search", response_model=list[CourseResult])
@limiter.limit("60/minute")
def search(
    request: Request,
    q: Annotated[
        str,
        Query(
            min_length=1,
            max_length=100,
            pattern=r"^[a-zA-Z0-9 \-]+$",
            description="Course code or title fragment. Max 100 chars, alphanumeric + space + hyphen.",
        ),
    ],
    db: Session = Depends(get_db),
) -> list[dict]:
    """Search courses by code or title. Returns up to 20 results. (API-01)"""
    return search_courses(db, q)


@router.get("/{course_id}/professors", response_model=list[ProfessorRanking])
@limiter.limit("60/minute")
def get_professors(
    request: Request,
    course_id: int,
    response: Response,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: Session = Depends(get_db),
) -> list[dict]:
    """Return professors for a course ranked by Gaucho Score, with raw factor values. (API-02)

    Scores are computed fresh per-request from raw GPA/RMP/sentiment data.
    Raw factors (gpa_factor, quality_factor, difficulty_factor, sentiment_factor) are
    included so the React frontend can rerank with custom weights client-side.
    Missing RateMyProfessors fields stay null and are omitted from the score.
    """
    profs = get_professors_for_course(db, course_id)
    if not profs:
        raise HTTPException(status_code=404, detail="Course not found or no professors on record")

    # Fetch schedule data for all professors in one query
    prof_ids = [p["id"] for p in profs]
    current_qcode, next_qcode = current_and_next_quarter_codes()

    # Query both current and next quarter so students see data regardless of
    # where we are in the academic calendar (e.g. mid-Spring still shows Spring).
    schedule_map_current = get_scheduled_sections(db, course_id, prof_ids, quarter_code=current_qcode)
    schedule_map_next = get_scheduled_sections(db, course_id, prof_ids, quarter_code=next_qcode)

    # Merge: prefer next quarter, fall back to current quarter
    schedule_map: dict[int, list[dict]] = {}
    all_prof_ids = set(schedule_map_current) | set(schedule_map_next)
    for pid in all_prof_ids:
        sections = schedule_map_next.get(pid, []) or schedule_map_current.get(pid, [])
        schedule_map[pid] = sections

    results = []
    for p in profs:
        gpa_f = normalize_gpa(p["mean_gpa"]) if p["mean_gpa"] is not None else None
        has_rmp = p["rmp_quality"] is not None

        if p["rmp_quality"] is not None and p["rmp_num_ratings"]:
            adj_qual = bayesian_adjust(p["rmp_quality"], p["rmp_num_ratings"], 3.0)
            qual_f = normalize_quality(adj_qual)
        elif p["rmp_quality"] is not None:
            qual_f = normalize_quality(p["rmp_quality"])
        else:
            qual_f = None

        diff_f = normalize_difficulty(p["rmp_difficulty"]) if p["rmp_difficulty"] is not None else None
        sent_f = (p["avg_sentiment"] + 1) / 2 if p["avg_sentiment"] is not None else None

        score = compute_gaucho_score(gpa_f, qual_f, diff_f, sent_f)

        prof_sections = schedule_map.get(p["id"], [])

        results.append({
            "id": p["id"],
            "name": p["name"],
            "department": p["department"],
            "gaucho_score": score,
            "gpa_factor": gpa_f,
            "quality_factor": qual_f,
            "difficulty_factor": diff_f,
            "sentiment_factor": sent_f,
            "has_rmp": has_rmp,
            "rmp_quality": p["rmp_quality"],
            "rmp_difficulty": p["rmp_difficulty"],
            "rmp_would_take_again": p["rmp_would_take_again"],
            "rmp_num_ratings": p["rmp_num_ratings"],
            "mean_gpa": p["mean_gpa"],
            "std_gpa": p["std_gpa"],
            "avg_sentiment": p["avg_sentiment"],
            "match_confidence": p["match_confidence"],
            "quarters_taught": p["quarters_taught"],
            "tags": p.get("tags", []),
            "is_active_teacher": p.get("is_active_teacher", False),
            "recent_quarters": p.get("recent_quarters", []),
            "teaching_next_quarter": len(prof_sections) > 0,
            "scheduled_sections": prof_sections,
        })

    ranked = sorted(results, key=lambda x: x["gaucho_score"], reverse=True)
    response.headers["X-Total-Count"] = str(len(ranked))
    return ranked[offset:offset + limit]


@router.get("/{course_id}/sections", response_model=list[ScheduledSectionResponse])
def get_course_sections(
    course_id: int,
    db: Session = Depends(get_db),
) -> list[dict]:
    """Return all scheduled sections for a course (current + next quarter).

    Filtered to sections with a named instructor and meeting time.
    """
    current_qcode, next_qcode = current_and_next_quarter_codes()

    sections = get_all_course_sections(db, course_id, [current_qcode, next_qcode])
    if not sections:
        return []
    return sections

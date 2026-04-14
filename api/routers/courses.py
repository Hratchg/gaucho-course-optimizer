from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas import CourseResult, ProfessorRanking
from dashboard.queries import get_professors_for_course, get_scheduled_sections, search_courses
from etl.scoring import (
    compute_gaucho_score,
    normalize_difficulty,
    normalize_gpa,
    normalize_quality,
)
from ucsb_api.client import get_next_quarter_code

router = APIRouter()


# IMPORTANT: /search must be declared BEFORE /{course_id}/professors.
# FastAPI matches routes in declaration order. If /{course_id} comes first,
# GET /courses/search?q=x would match with course_id="search" → 422 int parse error.


@router.get("/search", response_model=list[CourseResult])
def search(
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
def get_professors(
    course_id: int,
    db: Session = Depends(get_db),
) -> list[dict]:
    """Return professors for a course ranked by Gaucho Score, with raw factor values. (API-02)

    Scores are computed fresh per-request from raw GPA/RMP/sentiment data.
    Raw factors (gpa_factor, quality_factor, difficulty_factor, sentiment_factor) are
    included so the React frontend can rerank with custom weights client-side.
    """
    profs = get_professors_for_course(db, course_id)
    if not profs:
        raise HTTPException(status_code=404, detail="Course not found or no professors on record")

    # Fetch schedule data for all professors in one query
    prof_ids = [p["id"] for p in profs]
    # Determine next quarter code: try to derive from current date
    # Quarter codes: YYYYQ where Q: 1=Winter, 2=Spring, 3=Summer, 4=Fall
    import datetime as _dt
    now = _dt.date.today()
    month = now.month
    year = now.year
    if month <= 3:
        current_qcode = f"{year}1"  # Winter
    elif month <= 6:
        current_qcode = f"{year}2"  # Spring
    elif month <= 8:
        current_qcode = f"{year}3"  # Summer
    else:
        current_qcode = f"{year}4"  # Fall
    next_qcode = get_next_quarter_code(current_qcode)

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
        # None-safe factor computation — fall back to 0.5 (neutral) when data is missing
        gpa_f = normalize_gpa(p["mean_gpa"]) if p["mean_gpa"] is not None else 0.5
        qual_f = normalize_quality(p["rmp_quality"]) if p["rmp_quality"] is not None else 0.5
        diff_f = normalize_difficulty(p["rmp_difficulty"]) if p["rmp_difficulty"] is not None else 0.5

        # avg_sentiment is a VADER score in [-1, 1]. Map to [0, 1] before scoring.
        # Example: avg_sentiment=0.0 (neutral) → sent_f=0.5, not 0.0.
        sent_f = (p["avg_sentiment"] + 1) / 2 if p["avg_sentiment"] is not None else 0.5

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

    return sorted(results, key=lambda x: x["gaucho_score"], reverse=True)

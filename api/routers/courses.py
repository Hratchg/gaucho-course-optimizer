from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas import CourseResult, ProfessorRanking
from dashboard.queries import get_professors_for_course, search_courses
from etl.scoring import (
    compute_gaucho_score,
    normalize_difficulty,
    normalize_gpa,
    normalize_quality,
)

router = APIRouter()


# IMPORTANT: /search must be declared BEFORE /{course_id}/professors.
# FastAPI matches routes in declaration order. If /{course_id} comes first,
# GET /courses/search?q=x would match with course_id="search" → 422 int parse error.


@router.get("/search", response_model=list[CourseResult])
def search(
    q: Annotated[
        str,
        Query(
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
            "keywords": p.get("keywords", []),
        })

    return sorted(results, key=lambda x: x["gaucho_score"], reverse=True)

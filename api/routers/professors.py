from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas import CommentResult, GradeQuarter
from dashboard.queries import get_comments_for_professor, get_grade_history

router = APIRouter()


@router.get("/{professor_id}/grades", response_model=list[GradeQuarter])
def get_grades(
    professor_id: int,
    course_id: int = Query(..., description="Course ID — required to identify the specific professor+course pair"),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Return per-quarter grade distribution for a professor+course combination. (API-03)

    Both professor_id (path) and course_id (query) are required — grade data is
    specific to the (professor, course) pair, not just the professor.
    """
    grades = get_grade_history(db, professor_id, course_id)
    if not grades:
        raise HTTPException(
            status_code=404,
            detail=f"No grade data found for professor {professor_id} in course {course_id}",
        )
    return grades


@router.get("/{professor_id}/comments", response_model=list[CommentResult])
def get_comments(
    professor_id: int,
    limit: int = Query(default=5, ge=1, le=50, description="Max number of comments to return"),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Return the most recent RMP comments for a professor with VADER sentiment scores. (API-04)

    sentiment_score is the raw VADER compound score in [-1, 1].
    The React frontend applies its own display logic (positive/neutral/negative badge).
    Default limit is 5 per API-04 requirement.
    """
    comments = get_comments_for_professor(db, professor_id, limit=limit)
    if not comments:
        raise HTTPException(
            status_code=404,
            detail=f"No comments found for professor {professor_id}",
        )
    return comments

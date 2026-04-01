from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from db.models import Professor, Course, GradeDistribution, RmpRating, RmpComment

MONTH_NAMES = [
    "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def get_departments(session: Session) -> list[str]:
    """Get all distinct department names, sorted."""
    rows = session.query(Course.department).distinct().order_by(Course.department).all()
    return [r[0] for r in rows if r[0]]


def search_courses(session: Session, query: str, department: str | None = None) -> list[dict]:
    """Search courses by code or title fragment, optionally filtered by department."""
    pattern = f"%{query}%"
    q = session.query(Course).filter(
        or_(Course.code.ilike(pattern), Course.title.ilike(pattern))
    )
    if department:
        q = q.filter(Course.department == department)
    courses = q.order_by(Course.code).limit(20).all()
    return [{"id": c.id, "code": c.code, "title": c.title, "department": c.department} for c in courses]


def get_professors_for_course(session: Session, course_id: int, min_year: int | None = None) -> list[dict]:
    """Get all professors who have taught a course, with their stats. 2 queries max."""

    # Subquery: latest RMP rating per professor
    latest_rating_sq = (
        session.query(
            RmpRating.professor_id,
            func.max(RmpRating.id).label("latest_rating_id"),  # assumes max(id) == most recently fetched; valid for sequential ETL inserts
        )
        .group_by(RmpRating.professor_id)
        .subquery("latest_rating")
    )

    # Subquery: sentiment stats per RMP rating
    sentiment_sq = (
        session.query(
            RmpComment.rmp_rating_id,
            func.avg(RmpComment.sentiment_score).label("avg_sentiment"),
        )
        .filter(RmpComment.sentiment_score.isnot(None))
        .group_by(RmpComment.rmp_rating_id)
        .subquery("sentiment")
    )

    # Main query: professors + grade stats + RMP data + sentiment
    q = (
        session.query(
            Professor,
            func.avg(GradeDistribution.avg_gpa).label("mean_gpa"),
            func.stddev(GradeDistribution.avg_gpa).label("std_gpa"),
            func.count(GradeDistribution.id).label("quarters_taught"),
            RmpRating,
            sentiment_sq.c.avg_sentiment,
        )
        .join(GradeDistribution, GradeDistribution.professor_id == Professor.id)
        .filter(GradeDistribution.course_id == course_id)
        .outerjoin(latest_rating_sq, latest_rating_sq.c.professor_id == Professor.id)
        .outerjoin(RmpRating, RmpRating.id == latest_rating_sq.c.latest_rating_id)
        .outerjoin(sentiment_sq, sentiment_sq.c.rmp_rating_id == RmpRating.id)
    )
    if min_year is not None:
        q = q.filter(GradeDistribution.year >= min_year)
    results = q.group_by(Professor.id, RmpRating.id, sentiment_sq.c.avg_sentiment).all()

    # 2nd query: keywords grouped by rating_id (not N+1)
    rating_ids = [row[4].id for row in results if row[4] is not None]
    keywords_map = {}
    if rating_ids:
        keyword_rows = (
            session.query(RmpComment.rmp_rating_id, RmpComment.keywords)
            .filter(RmpComment.rmp_rating_id.in_(rating_ids), RmpComment.keywords.isnot(None))
            .all()
        )
        for rating_id, kw in keyword_rows:
            if isinstance(kw, list):
                keywords_map.setdefault(rating_id, []).extend(kw)

    professors = []
    for prof, mean_gpa, std_gpa, quarters_taught, rmp, avg_sentiment in results:
        kw_list = keywords_map.get(rmp.id, []) if rmp else []
        professors.append({
            "id": prof.id,
            "name": prof.name_rmp or prof.name_nexus or "Unknown",
            "department": prof.department,
            "mean_gpa": round(float(mean_gpa), 2) if mean_gpa else None,
            "std_gpa": round(float(std_gpa), 2) if std_gpa else None,
            "quarters_taught": quarters_taught,
            "rmp_quality": rmp.overall_quality if rmp else None,
            "rmp_difficulty": rmp.difficulty if rmp else None,
            "rmp_would_take_again": rmp.would_take_again_pct if rmp else None,
            "rmp_num_ratings": rmp.num_ratings if rmp else None,
            "avg_sentiment": round(float(avg_sentiment), 2) if avg_sentiment is not None else None,
            "keywords": list(set(kw_list))[:8],
            "match_confidence": prof.match_confidence,
        })

    return professors


def get_grade_history(session: Session, professor_id: int, course_id: int) -> list[dict]:
    """Get quarter-by-quarter grade history for a professor+course."""
    grades = (
        session.query(GradeDistribution)
        .filter_by(professor_id=professor_id, course_id=course_id)
        .order_by(GradeDistribution.year, GradeDistribution.quarter)
        .all()
    )
    return [
        {
            "quarter": f"{g.quarter} {g.year}",
            "avg_gpa": g.avg_gpa,
            "a_plus": g.a_plus, "a": g.a, "a_minus": g.a_minus,
            "b_plus": g.b_plus, "b": g.b, "b_minus": g.b_minus,
            "c_plus": g.c_plus, "c": g.c, "c_minus": g.c_minus,
            "d_plus": g.d_plus, "d": g.d, "d_minus": g.d_minus,
            "f": g.f,
        }
        for g in grades
    ]


def get_comments_for_professor(session: Session, professor_id: int, limit: int = 5) -> list[dict]:
    """Fetch the most recent RMP comments for a professor."""
    comments = (
        session.query(RmpComment)
        .join(RmpRating, RmpComment.rmp_rating_id == RmpRating.id)
        .filter(RmpRating.professor_id == professor_id)
        .order_by(RmpComment.created_at.desc().nullslast())
        .limit(limit)
        .all()
    )
    results = []
    for c in comments:
        if c.created_at:
            formatted_date = f"{MONTH_NAMES[c.created_at.month]} {c.created_at.year}"
        else:
            formatted_date = None
        results.append({
            "text": c.comment_text,
            "sentiment_score": c.sentiment_score,
            "keywords": c.keywords,
            "created_at": formatted_date,
        })
    return results

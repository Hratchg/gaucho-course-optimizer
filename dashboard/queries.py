from datetime import datetime

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
    """Get all professors who have taught a course, with their stats. 3 queries max."""

    cutoff_year = datetime.now().year - 3

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

    # Subquery: count distinct (quarter, year) pairs in recent years per professor
    recent_grades_sq = (
        session.query(
            GradeDistribution.professor_id,
            GradeDistribution.quarter,
            GradeDistribution.year,
        )
        .filter(
            GradeDistribution.course_id == course_id,
            GradeDistribution.year >= cutoff_year,
        )
        .group_by(GradeDistribution.professor_id, GradeDistribution.quarter, GradeDistribution.year)
        .subquery("recent_distinct")
    )
    # Wrap to count the distinct quarter-year pairs per professor
    active_teaching_sq = (
        session.query(
            recent_grades_sq.c.professor_id,
            func.count().label("distinct_recent_quarters"),
        )
        .group_by(recent_grades_sq.c.professor_id)
        .subquery("active_teaching")
    )

    # Main query: professors + grade stats + RMP data + sentiment + active teaching
    q = (
        session.query(
            Professor,
            func.avg(GradeDistribution.avg_gpa).label("mean_gpa"),
            func.stddev(GradeDistribution.avg_gpa).label("std_gpa"),
            func.count(GradeDistribution.id).label("quarters_taught"),
            RmpRating,
            sentiment_sq.c.avg_sentiment,
            active_teaching_sq.c.distinct_recent_quarters,
        )
        .join(GradeDistribution, GradeDistribution.professor_id == Professor.id)
        .filter(GradeDistribution.course_id == course_id)
        .outerjoin(latest_rating_sq, latest_rating_sq.c.professor_id == Professor.id)
        .outerjoin(RmpRating, RmpRating.id == latest_rating_sq.c.latest_rating_id)
        .outerjoin(sentiment_sq, sentiment_sq.c.rmp_rating_id == RmpRating.id)
        .outerjoin(active_teaching_sq, active_teaching_sq.c.professor_id == Professor.id)
    )
    if min_year is not None:
        q = q.filter(GradeDistribution.year >= min_year)
    results = q.group_by(
        Professor.id, RmpRating.id, sentiment_sq.c.avg_sentiment,
        active_teaching_sq.c.distinct_recent_quarters,
    ).all()

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

    # 3rd query: recent quarters per professor for this course
    prof_ids = [row[0].id for row in results]
    quarters_map: dict[int, list[str]] = {}
    if prof_ids:
        quarter_order = {"Fall": 4, "Summer": 3, "Spring": 2, "Winter": 1}
        quarter_rows = (
            session.query(
                GradeDistribution.professor_id,
                GradeDistribution.quarter,
                GradeDistribution.year,
            )
            .filter(
                GradeDistribution.course_id == course_id,
                GradeDistribution.year >= cutoff_year,
                GradeDistribution.professor_id.in_(prof_ids),
            )
            .distinct()
            .all()
        )
        raw_map: dict[int, list[tuple[str, int]]] = {}
        for pid, q_name, y in quarter_rows:
            raw_map.setdefault(pid, []).append((q_name, y))
        for pid in raw_map:
            raw_map[pid].sort(key=lambda x: (x[1], quarter_order.get(x[0], 0)), reverse=True)
            quarters_map[pid] = [f"{q_name} {y}" for q_name, y in raw_map[pid]]

    professors = []
    for prof, mean_gpa, std_gpa, quarters_taught, rmp, avg_sentiment, active_count in results:
        kw_list = keywords_map.get(rmp.id, []) if rmp else []
        distinct_recent = active_count if active_count else 0
        is_active = distinct_recent >= 3
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
            "is_active_teacher": is_active,
            "recent_quarters": quarters_map.get(prof.id, []),
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

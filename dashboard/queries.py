from sqlalchemy import func
from sqlalchemy.orm import Session
from db.models import Professor, Course, GradeDistribution, RmpRating, RmpComment


def search_courses(session: Session, query: str) -> list[dict]:
    """Search courses by code prefix."""
    courses = (
        session.query(Course)
        .filter(Course.code.ilike(f"%{query}%"))
        .order_by(Course.code)
        .limit(20)
        .all()
    )
    return [{"id": c.id, "code": c.code, "title": c.title, "department": c.department} for c in courses]


def get_professors_for_course(session: Session, course_id: int) -> list[dict]:
    """Get all professors who have taught a course, with their stats."""
    results = (
        session.query(
            Professor,
            func.avg(GradeDistribution.avg_gpa).label("mean_gpa"),
            func.stddev(GradeDistribution.avg_gpa).label("std_gpa"),
            func.count(GradeDistribution.id).label("quarters_taught"),
        )
        .join(GradeDistribution, GradeDistribution.professor_id == Professor.id)
        .filter(GradeDistribution.course_id == course_id)
        .group_by(Professor.id)
        .all()
    )

    professors = []
    for prof, mean_gpa, std_gpa, quarters_taught in results:
        # Get latest RMP rating
        rmp = (
            session.query(RmpRating)
            .filter_by(professor_id=prof.id)
            .order_by(RmpRating.fetched_at.desc())
            .first()
        )

        # Get sentiment stats
        avg_sentiment = None
        keywords = []
        if rmp:
            sentiment_result = (
                session.query(func.avg(RmpComment.sentiment_score))
                .filter(RmpComment.rmp_rating_id == rmp.id)
                .scalar()
            )
            avg_sentiment = float(sentiment_result) if sentiment_result else None

            keyword_rows = (
                session.query(RmpComment.keywords)
                .filter(RmpComment.rmp_rating_id == rmp.id, RmpComment.keywords.isnot(None))
                .all()
            )
            for (kw,) in keyword_rows:
                if isinstance(kw, list):
                    keywords.extend(kw)

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
            "avg_sentiment": round(avg_sentiment, 2) if avg_sentiment else None,
            "keywords": list(set(keywords))[:8],
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

from datetime import datetime, timezone
from db.models import Professor, RmpRating, RmpComment


def load_rmp_teacher_to_db(teacher: dict, session) -> Professor:
    """Load a parsed RMP teacher dict into the database."""
    rmp_id = teacher["legacy_id"]
    name_rmp = f"{teacher['first_name']} {teacher['last_name']}"

    # Get or create professor by rmp_id
    prof = session.query(Professor).filter_by(rmp_id=rmp_id).first()
    if prof is None:
        prof = Professor(
            name_rmp=name_rmp,
            rmp_id=rmp_id,
            department=teacher.get("department", ""),
        )
        session.add(prof)
        session.flush()
    else:
        prof.name_rmp = name_rmp
        prof.department = teacher.get("department", prof.department)

    # Upsert rating
    rating = RmpRating(
        professor_id=prof.id,
        overall_quality=teacher.get("avg_rating"),
        difficulty=teacher.get("avg_difficulty"),
        would_take_again_pct=teacher.get("would_take_again_pct"),
        num_ratings=teacher.get("num_ratings", 0),
        fetched_at=datetime.now(timezone.utc),
    )
    session.add(rating)
    session.flush()

    # Add comments
    for comment in teacher.get("comments", []):
        if not comment.get("text"):
            continue
        rmp_comment = RmpComment(
            rmp_rating_id=rating.id,
            comment_text=comment["text"],
            created_at=datetime.fromisoformat(comment["date"]) if comment.get("date") else None,
        )
        session.add(rmp_comment)

    session.commit()
    return prof

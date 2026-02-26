import re
from datetime import datetime, timezone, timedelta
from db.models import Professor, RmpRating, RmpComment, GradeDistribution


def _parse_rmp_date(date_str: str | None) -> datetime | None:
    """Parse RMP date strings like '2018-06-24 00:57:13 +0000 UTC'."""
    if not date_str:
        return None
    # Strip trailing timezone label (e.g. " UTC")
    cleaned = re.sub(r"\s+[A-Z]{2,4}$", "", date_str.strip())
    # Strip offset like " +0000" and parse as UTC
    cleaned = re.sub(r"\s+[+-]\d{4}$", "", cleaned)
    try:
        return datetime.strptime(cleaned, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        try:
            return datetime.fromisoformat(date_str)
        except ValueError:
            return None


def get_active_professors(session, min_year: int = 2023) -> list[Professor]:
    """Get professors who have taught at least one course since min_year."""
    return (
        session.query(Professor)
        .join(GradeDistribution, GradeDistribution.professor_id == Professor.id)
        .filter(GradeDistribution.year >= min_year)
        .group_by(Professor.id)
        .all()
    )


def is_stale(fetched_at: datetime | None, max_age_days: int = 2) -> bool:
    """Check if an RMP rating is stale (older than max_age_days or missing)."""
    if fetched_at is None:
        return True
    if fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=timezone.utc)
    age = datetime.now(timezone.utc) - fetched_at
    return age > timedelta(days=max_age_days)


def load_rmp_teacher_to_db(
    teacher: dict,
    session,
    nexus_professor_id: int | None = None,
    match_confidence: int | None = None,
) -> Professor:
    """Load a parsed RMP teacher dict into the database.

    If nexus_professor_id is provided, link RMP data to the existing Nexus professor
    instead of creating a new professor record.
    """
    rmp_id = teacher["legacy_id"]
    name_rmp = f"{teacher['first_name']} {teacher['last_name']}"

    if nexus_professor_id is not None:
        # Link to existing Nexus professor
        prof = session.get(Professor, nexus_professor_id)
        if prof is None:
            raise ValueError(f"No professor with id={nexus_professor_id}")
        # Check if another professor already has this rmp_id
        existing = session.query(Professor).filter_by(rmp_id=rmp_id).first()
        if existing and existing.id != nexus_professor_id:
            raise ValueError(
                f"RMP ID {rmp_id} already linked to professor id={existing.id} "
                f"({existing.name_nexus})"
            )
        prof.rmp_id = rmp_id
        prof.name_rmp = name_rmp
        if match_confidence is not None:
            prof.match_confidence = match_confidence
    else:
        # Fallback: get or create by rmp_id (original behavior)
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
            created_at=_parse_rmp_date(comment.get("date")),
        )
        session.add(rmp_comment)

    session.commit()
    return prof

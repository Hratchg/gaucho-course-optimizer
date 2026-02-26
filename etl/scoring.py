def normalize_gpa(gpa: float, dept_median: float = 3.0, dept_max: float = 4.0) -> float:
    """Normalize GPA to 0-1 relative to department stats."""
    if dept_max == 0:
        return 0.0
    return max(0.0, min(1.0, gpa / dept_max))


def normalize_quality(quality: float) -> float:
    """Normalize RMP quality (0-5) to 0-1."""
    return max(0.0, min(1.0, quality / 5.0))


def normalize_difficulty(difficulty: float) -> float:
    """Normalize RMP difficulty (0-5) to 0-1, inverted (lower difficulty = higher score)."""
    return max(0.0, min(1.0, (5.0 - difficulty) / 5.0))


def bayesian_adjust(value: float, count: int, prior: float, min_count: int = 5) -> float:
    """Bayesian adjustment: pull toward prior when sample size is small."""
    return (count * value + min_count * prior) / (count + min_count)


def compute_gaucho_score(
    gpa_factor: float,
    quality_factor: float,
    difficulty_factor: float,
    sentiment_factor: float,
    weights: dict[str, float] | None = None,
) -> float:
    """Compute Gaucho Value Score (0-100) from normalized factors and weights."""
    if weights is None:
        weights = {"gpa": 0.25, "quality": 0.25, "difficulty": 0.25, "sentiment": 0.25}

    raw = (
        gpa_factor * weights.get("gpa", 0.25)
        + quality_factor * weights.get("quality", 0.25)
        + difficulty_factor * weights.get("difficulty", 0.25)
        + sentiment_factor * weights.get("sentiment", 0.25)
    )
    return round(max(0.0, min(100.0, raw * 100)), 2)


def compute_all_scores(
    session,
    weights: dict[str, float] | None = None,
) -> dict:
    """Compute Gaucho Scores for all matched professors (those with both grades and RMP data).

    Returns stats dict: {computed, skipped}.
    """
    from datetime import datetime, timezone
    from sqlalchemy import func
    from db.models import (
        Professor, Course, GradeDistribution, RmpRating, RmpComment, GauchoScore,
    )

    if weights is None:
        weights = {"gpa": 0.25, "quality": 0.25, "difficulty": 0.25, "sentiment": 0.25}

    stats = {"computed": 0, "skipped": 0}

    # Find all (professor, course) pairs where professor has RMP data
    pairs = (
        session.query(
            Professor.id,
            GradeDistribution.course_id,
            func.avg(GradeDistribution.avg_gpa).label("mean_gpa"),
        )
        .join(GradeDistribution, GradeDistribution.professor_id == Professor.id)
        .join(RmpRating, RmpRating.professor_id == Professor.id)
        .filter(Professor.rmp_id.isnot(None))
        .group_by(Professor.id, GradeDistribution.course_id)
        .all()
    )

    for prof_id, course_id, mean_gpa in pairs:
        # Get latest RMP rating
        rating = (
            session.query(RmpRating)
            .filter_by(professor_id=prof_id)
            .order_by(RmpRating.fetched_at.desc())
            .first()
        )
        if not rating:
            stats["skipped"] += 1
            continue

        # Compute factors
        gpa_f = normalize_gpa(float(mean_gpa)) if mean_gpa else 0.5
        qual_f = normalize_quality(rating.overall_quality) if rating.overall_quality else 0.5
        diff_f = normalize_difficulty(rating.difficulty) if rating.difficulty else 0.5

        # Sentiment: average of comments
        avg_sentiment = (
            session.query(func.avg(RmpComment.sentiment_score))
            .join(RmpRating, RmpComment.rmp_rating_id == RmpRating.id)
            .filter(RmpRating.professor_id == prof_id, RmpComment.sentiment_score.isnot(None))
            .scalar()
        )
        sent_f = (float(avg_sentiment) + 1) / 2 if avg_sentiment is not None else 0.5

        # Bayesian adjust quality
        if rating.overall_quality and rating.num_ratings:
            adj_qual = bayesian_adjust(rating.overall_quality, rating.num_ratings, 3.0)
            qual_f = normalize_quality(adj_qual)

        score = compute_gaucho_score(gpa_f, qual_f, diff_f, sent_f, weights)

        # Upsert: delete old score for this pair, insert new
        session.query(GauchoScore).filter_by(
            professor_id=prof_id, course_id=course_id,
        ).delete()

        session.add(GauchoScore(
            professor_id=prof_id,
            course_id=course_id,
            score=score,
            weights_used=weights,
            computed_at=datetime.now(timezone.utc),
        ))
        stats["computed"] += 1

    session.commit()
    return stats

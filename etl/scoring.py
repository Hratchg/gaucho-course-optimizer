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
    """Compute Gaucho Scores for all matched professors via a single bulk JOIN.

    Replaces the former N+1 loop (3 queries × 11,750 pairs = ~35k queries).
    Loads all data in one query, computes scores in Python, bulk-upserts results.

    Returns stats dict: {computed, skipped}.
    """
    from datetime import datetime, timezone
    from sqlalchemy import func
    from db.models import (
        Professor, GradeDistribution, RmpRating, RmpComment, GauchoScore,
    )

    if weights is None:
        weights = {"gpa": 0.25, "quality": 0.25, "difficulty": 0.25, "sentiment": 0.25}

    stats = {"computed": 0, "skipped": 0}

    # Subquery 1: latest RMP rating id per professor
    latest_rating_sq = (
        session.query(
            RmpRating.professor_id,
            func.max(RmpRating.id).label("latest_rating_id"),  # MAX(id) is valid "latest" proxy: rmp_loader always inserts a new row on re-scrape, so IDs are monotonically increasing
        )
        .group_by(RmpRating.professor_id)
        .subquery("latest_rating")
    )

    # Subquery 2: avg sentiment per rmp_rating_id
    sentiment_sq = (
        session.query(
            RmpComment.rmp_rating_id,
            func.avg(RmpComment.sentiment_score).label("avg_sentiment"),
        )
        .filter(RmpComment.sentiment_score.isnot(None))
        .group_by(RmpComment.rmp_rating_id)
        .subquery("sentiment")
    )

    # Single bulk JOIN: professors + grade avg + latest RMP + avg sentiment
    rows = (
        session.query(
            Professor.id.label("professor_id"),
            GradeDistribution.course_id,
            func.avg(GradeDistribution.avg_gpa).label("mean_gpa"),
            RmpRating.overall_quality,
            RmpRating.difficulty,
            RmpRating.num_ratings,
            sentiment_sq.c.avg_sentiment,
        )
        .join(GradeDistribution, GradeDistribution.professor_id == Professor.id)
        .join(latest_rating_sq, latest_rating_sq.c.professor_id == Professor.id)
        .join(RmpRating, RmpRating.id == latest_rating_sq.c.latest_rating_id)
        .outerjoin(sentiment_sq, sentiment_sq.c.rmp_rating_id == RmpRating.id)
        # Professors with no RmpRating rows are excluded by the INNER JOIN (not counted in skipped). 'skipped' means a row was reached but had null quality.
        .filter(Professor.rmp_id.isnot(None))
        # RMP columns are 1:1 per rating join; included in GROUP BY as required by SQLAlchemy legacy query() API
        .group_by(
            Professor.id,
            GradeDistribution.course_id,
            RmpRating.overall_quality,
            RmpRating.difficulty,
            RmpRating.num_ratings,
            sentiment_sq.c.avg_sentiment,
        )
        .all()
    )

    # Compute scores in Python, bulk-upsert
    for row in rows:
        prof_id = row.professor_id
        course_id = row.course_id
        mean_gpa = row.mean_gpa
        quality = row.overall_quality
        difficulty = row.difficulty
        num_ratings = row.num_ratings
        avg_sentiment = row.avg_sentiment

        if quality is None:
            stats["skipped"] += 1
            continue

        gpa_f = normalize_gpa(float(mean_gpa)) if mean_gpa else 0.5
        qual_f = normalize_quality(quality) if quality else 0.5
        diff_f = normalize_difficulty(difficulty) if difficulty else 0.5
        sent_f = (float(avg_sentiment) + 1) / 2 if avg_sentiment is not None else 0.5

        # Bayesian adjust quality factor
        if quality and num_ratings:
            adj_qual = bayesian_adjust(quality, num_ratings, 3.0)
            qual_f = normalize_quality(adj_qual)

        score = compute_gaucho_score(gpa_f, qual_f, diff_f, sent_f, weights)

        # Upsert: delete old record for this (professor, course) pair, insert new
        session.query(GauchoScore).filter_by(
            professor_id=prof_id,
            course_id=course_id,
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

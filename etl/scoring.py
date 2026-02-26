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

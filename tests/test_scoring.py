from etl.scoring import compute_gaucho_score, normalize_gpa, normalize_quality, normalize_difficulty, bayesian_adjust


def test_normalize_gpa():
    # 4.0 GPA in a dept with median 3.0 → high score
    assert normalize_gpa(4.0, dept_median=3.0, dept_max=4.0) > 0.8
    # 2.0 GPA → moderate-low score (2.0/4.0 = 0.5)
    assert normalize_gpa(2.0, dept_median=3.0, dept_max=4.0) == 0.5


def test_normalize_quality():
    assert normalize_quality(5.0) == 1.0
    assert normalize_quality(0.0) == 0.0
    assert normalize_quality(2.5) == 0.5


def test_normalize_difficulty():
    # Low difficulty → high score (inverted)
    assert normalize_difficulty(1.0) > 0.7
    # High difficulty → low score
    assert normalize_difficulty(5.0) == 0.0


def test_bayesian_adjust():
    # Professor with many ratings → stays close to their value
    adjusted = bayesian_adjust(value=4.5, count=50, prior=3.0, min_count=5)
    assert abs(adjusted - 4.5) < 0.3

    # Professor with 1 rating → pulled heavily toward prior
    adjusted = bayesian_adjust(value=5.0, count=1, prior=3.0, min_count=5)
    assert adjusted < 4.0


def test_compute_gaucho_score_equal_weights():
    score = compute_gaucho_score(
        gpa_factor=0.8, quality_factor=0.9,
        difficulty_factor=0.7, sentiment_factor=0.6,
        weights={"gpa": 0.25, "quality": 0.25, "difficulty": 0.25, "sentiment": 0.25},
    )
    expected = (0.8 * 0.25 + 0.9 * 0.25 + 0.7 * 0.25 + 0.6 * 0.25) * 100
    assert abs(score - expected) < 0.01


def test_compute_gaucho_score_custom_weights():
    # All weight on GPA
    score = compute_gaucho_score(
        gpa_factor=1.0, quality_factor=0.0,
        difficulty_factor=0.0, sentiment_factor=0.0,
        weights={"gpa": 1.0, "quality": 0.0, "difficulty": 0.0, "sentiment": 0.0},
    )
    assert score == 100.0

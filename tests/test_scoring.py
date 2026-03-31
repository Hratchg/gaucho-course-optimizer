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


def test_known_inputs_all_half():
    """All factors at 0.5, equal weights => exactly 50.0."""
    score = compute_gaucho_score(0.5, 0.5, 0.5, 0.5)
    assert score == 50.0


def test_known_inputs_all_max():
    """All factors at 1.0, equal weights => exactly 100.0."""
    score = compute_gaucho_score(1.0, 1.0, 1.0, 1.0)
    assert score == 100.0


def test_known_inputs_all_zero():
    """All factors at 0.0 => exactly 0.0."""
    score = compute_gaucho_score(0.0, 0.0, 0.0, 0.0)
    assert score == 0.0


def test_normalize_gpa_exact():
    """normalize_gpa(3.52) = 3.52/4.0 = 0.88."""
    assert normalize_gpa(3.52) == 0.88


def test_normalize_quality_exact():
    """normalize_quality(4.2) = 4.2/5.0 = 0.84."""
    assert abs(normalize_quality(4.2) - 0.84) < 1e-10


def test_normalize_difficulty_exact():
    """normalize_difficulty(3.1) = (5.0-3.1)/5.0 = 0.38."""
    assert normalize_difficulty(3.1) == 0.38


def test_full_known_case():
    """Known professor: GPA 3.52, quality 4.2, difficulty 3.1, sentiment 0.65."""
    gpa_f = normalize_gpa(3.52)
    qual_f = normalize_quality(4.2)
    diff_f = normalize_difficulty(3.1)
    sent_f = (0.65 + 1) / 2  # 0.825
    score = compute_gaucho_score(gpa_f, qual_f, diff_f, sent_f)
    expected = round((gpa_f * 0.25 + qual_f * 0.25 + diff_f * 0.25 + sent_f * 0.25) * 100, 2)
    assert score == expected


def test_bayesian_adjust_zero_count():
    """With count=0, result should equal the prior."""
    result = bayesian_adjust(value=5.0, count=0, prior=3.0, min_count=5)
    assert result == 3.0


def test_score_clamps_to_range():
    """Score should be clamped to 0-100 range."""
    assert compute_gaucho_score(0.0, 0.0, 0.0, 0.0) == 0.0
    assert compute_gaucho_score(1.0, 1.0, 1.0, 1.0) == 100.0
    assert compute_gaucho_score(-1.0, -1.0, -1.0, -1.0) >= 0.0


def test_score_with_gpa_only_weight():
    """All weight on GPA, GPA factor 0.75 => score should be 75.0."""
    score = compute_gaucho_score(
        gpa_factor=0.75, quality_factor=0.0,
        difficulty_factor=0.0, sentiment_factor=0.0,
        weights={"gpa": 1.0, "quality": 0.0, "difficulty": 0.0, "sentiment": 0.0},
    )
    assert score == 75.0

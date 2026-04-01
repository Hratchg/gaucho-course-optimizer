import pytest
from etl.scoring import (
    compute_gaucho_score,
    normalize_gpa,
    normalize_quality,
    normalize_difficulty,
    bayesian_adjust,
    compute_all_scores,
)
from db.models import Professor, Course, GradeDistribution, RmpRating, RmpComment, GauchoScore


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


# ---------------------------------------------------------------------------
# Integration tests: compute_all_scores() with an in-memory SQLite session
#
# These tests use a fresh SQLite in-memory DB so they:
#   1. Run fast (no network round-trip)
#   2. Are fully isolated (no production data visible)
#   3. Test the bulk JOIN logic end-to-end via SQLAlchemy ORM
# ---------------------------------------------------------------------------

@pytest.fixture
def mem_session():
    """Provide a fully isolated SQLite in-memory session for scoring integration tests."""
    from sqlalchemy import create_engine as _create_engine
    from sqlalchemy.orm import sessionmaker as _sessionmaker
    from db.models import Base

    engine = _create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = _sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


def _seed_matched_professor(session):
    """Insert one professor with grades + RMP rating. Returns (professor, course)."""
    prof = Professor(name_nexus="Prof A", name_rmp="Prof A", rmp_id=1001, department="CS")
    course = Course(code="CS101", title="Intro CS", department="CS")
    session.add_all([prof, course])
    session.flush()

    grade = GradeDistribution(
        professor_id=prof.id, course_id=course.id,
        quarter="Fall", year=2023, avg_gpa=3.5,
    )
    rating = RmpRating(
        professor_id=prof.id,
        overall_quality=4.0,
        difficulty=2.5,
        num_ratings=20,
    )
    session.add_all([grade, rating])
    session.flush()
    return prof, course


def test_compute_all_scores_returns_computed(mem_session):
    """Test 1: compute_all_scores with seeded data returns computed > 0, skipped == 0."""
    _seed_matched_professor(mem_session)
    result = compute_all_scores(mem_session)
    assert isinstance(result, dict)
    assert "computed" in result
    assert "skipped" in result
    assert result["computed"] > 0
    assert result["skipped"] == 0


def test_compute_all_scores_skips_professor_without_rmp_rating(mem_session):
    """Test 2: professor with rmp_id but overall_quality=None is counted in skipped."""
    prof = Professor(name_nexus="Prof B", name_rmp="Prof B", rmp_id=1002, department="Math")
    course = Course(code="MATH101", title="Calculus", department="Math")
    mem_session.add_all([prof, course])
    mem_session.flush()

    grade = GradeDistribution(
        professor_id=prof.id, course_id=course.id,
        quarter="Fall", year=2023, avg_gpa=3.2,
    )
    # RmpRating exists but overall_quality is None
    rating = RmpRating(
        professor_id=prof.id,
        overall_quality=None,
        difficulty=None,
        num_ratings=0,
    )
    mem_session.add_all([grade, rating])
    mem_session.flush()

    result = compute_all_scores(mem_session)
    assert result["skipped"] >= 1


def test_compute_all_scores_no_duplicates_on_second_call(mem_session):
    """Test 3: calling compute_all_scores twice does not create duplicate GauchoScore rows."""
    prof, course = _seed_matched_professor(mem_session)

    compute_all_scores(mem_session)
    compute_all_scores(mem_session)

    count = (
        mem_session.query(GauchoScore)
        .filter_by(professor_id=prof.id, course_id=course.id)
        .count()
    )
    assert count == 1


def test_compute_all_scores_return_dict_always_has_both_keys(mem_session):
    """Test 4: return dict always has both 'computed' and 'skipped' integer keys."""
    # Empty DB — no professors at all
    result = compute_all_scores(mem_session)
    assert "computed" in result
    assert "skipped" in result
    assert isinstance(result["computed"], int)
    assert isinstance(result["skipped"], int)

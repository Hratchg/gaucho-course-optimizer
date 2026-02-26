"""End-to-end integration test: CSV → DB → name match → NLP → score."""
from db.models import Professor, Course, GradeDistribution, RmpRating, RmpComment
from scrapers.grades_loader import load_grades_to_db
from scrapers.rmp_loader import load_rmp_teacher_to_db
from etl.name_matcher import match_names
from etl.nlp_processor import analyze_sentiment, extract_keywords
from etl.scoring import compute_gaucho_score, normalize_gpa, normalize_quality, normalize_difficulty


def test_full_pipeline(db_session):
    # 1. Load grades
    grade_rows = [
        {
            "instructor": "SMITH, JOHN",
            "course_code": "PSTAT120A",
            "quarter": "Fall", "year": 2023,
            "a_plus": 3, "a": 12, "a_minus": 8,
            "b_plus": 5, "b": 4, "b_minus": 2,
            "c_plus": 1, "c": 0, "c_minus": 0,
            "d_plus": 0, "d": 0, "d_minus": 0, "f": 0,
            "avg_gpa": 3.52, "department": "PSTAT",
        },
    ]
    load_grades_to_db(grade_rows, db_session)

    # 2. Load RMP data
    teacher = {
        "legacy_id": 5555,
        "first_name": "John",
        "last_name": "Smith",
        "department": "Statistics",
        "avg_rating": 4.2,
        "avg_difficulty": 3.1,
        "would_take_again_pct": 85.0,
        "num_ratings": 42,
        "comments": [
            {"text": "Great professor, clear lectures!", "date": "2024-01-15"},
            {"text": "Tough grader but you learn a lot.", "date": "2024-03-20"},
        ],
    }
    load_rmp_teacher_to_db(teacher, db_session)

    # 3. Name matching
    nexus_names = ["SMITH, JOHN"]
    rmp_names = ["John Smith"]
    matches = match_names(nexus_names, rmp_names)
    assert "SMITH, JOHN" in matches
    assert matches["SMITH, JOHN"]["confidence"] >= 85

    # 4. NLP
    sentiment_1 = analyze_sentiment("Great professor, clear lectures!")
    assert sentiment_1 > 0
    keywords = extract_keywords(["Great professor, clear lectures!", "Tough grader but you learn a lot."])
    assert len(keywords) > 0

    # 5. Scoring
    score = compute_gaucho_score(
        gpa_factor=normalize_gpa(3.52),
        quality_factor=normalize_quality(4.2),
        difficulty_factor=normalize_difficulty(3.1),
        sentiment_factor=(sentiment_1 + 1) / 2,
    )
    assert 0 <= score <= 100
    assert score > 50  # Should be a decent professor

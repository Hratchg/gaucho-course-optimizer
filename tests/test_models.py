from db.models import Base, Professor, Course, GradeDistribution, RmpRating, RmpComment, GauchoScore


def test_all_tables_defined():
    table_names = {t.name for t in Base.metadata.sorted_tables}
    expected = {"professors", "courses", "grade_distributions", "rmp_ratings", "rmp_comments", "gaucho_scores"}
    assert expected == table_names


def test_professor_columns():
    cols = {c.name for c in Professor.__table__.columns}
    assert "name_nexus" in cols
    assert "name_rmp" in cols
    assert "rmp_id" in cols
    assert "department" in cols
    assert "match_confidence" in cols


def test_grade_distribution_has_letter_grades():
    cols = {c.name for c in GradeDistribution.__table__.columns}
    for grade in ["a_plus", "a", "a_minus", "b_plus", "b", "b_minus",
                  "c_plus", "c", "c_minus", "d_plus", "d", "d_minus", "f"]:
        assert grade in cols
    assert "avg_gpa" in cols

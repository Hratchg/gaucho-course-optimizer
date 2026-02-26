from db.models import Professor, Course, GradeDistribution
from scrapers.grades_loader import load_grades_to_db


def test_load_creates_professors_and_courses(db_session):
    rows = [
        {
            "instructor": "SMITH, JOHN",
            "course_code": "PSTAT120A",
            "quarter": "Fall",
            "year": 2023,
            "a_plus": 5, "a": 10, "a_minus": 8,
            "b_plus": 6, "b": 4, "b_minus": 2,
            "c_plus": 1, "c": 1, "c_minus": 0,
            "d_plus": 0, "d": 0, "d_minus": 0, "f": 0,
            "avg_gpa": 3.45,
            "department": "PSTAT",
        }
    ]
    load_grades_to_db(rows, db_session)

    profs = db_session.query(Professor).all()
    assert len(profs) == 1
    assert profs[0].name_nexus == "SMITH, JOHN"

    courses = db_session.query(Course).all()
    assert len(courses) == 1
    assert courses[0].code == "PSTAT120A"

    grades = db_session.query(GradeDistribution).all()
    assert len(grades) == 1
    assert grades[0].avg_gpa == 3.45


def test_load_is_idempotent(db_session):
    row = {
        "instructor": "DOE, JANE",
        "course_code": "CMPSC8",
        "quarter": "Winter",
        "year": 2024,
        "a_plus": 2, "a": 5, "a_minus": 3,
        "b_plus": 4, "b": 3, "b_minus": 1,
        "c_plus": 0, "c": 0, "c_minus": 0,
        "d_plus": 0, "d": 0, "d_minus": 0, "f": 0,
        "avg_gpa": 3.5,
        "department": "CMPSC",
    }
    load_grades_to_db([row], db_session)
    load_grades_to_db([row], db_session)

    grades = db_session.query(GradeDistribution).filter_by(
        quarter="Winter", year=2024
    ).all()
    # Should not duplicate
    assert len(grades) == 1

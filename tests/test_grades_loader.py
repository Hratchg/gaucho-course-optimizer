from sqlalchemy import event

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


def _row(instructor="DOE J", code="CMPSC8", quarter="Winter", year=2024, dept="CMPSC"):
    return {
        "instructor": instructor, "course_code": code, "quarter": quarter, "year": year,
        "a_plus": 1, "a": 2, "a_minus": 0, "b_plus": 0, "b": 1, "b_minus": 0,
        "c_plus": 0, "c": 0, "c_minus": 0, "d_plus": 0, "d": 0, "d_minus": 0, "f": 0,
        "avg_gpa": 3.75, "department": dept,
    }


def test_load_reuses_existing_professor_and_course(db_session):
    """Grades attach to rows the schedule sync or an earlier load already created."""
    prof = Professor(name_nexus="DOE J", department="CMPSC")
    course = Course(code="CMPSC8", department="CMPSC")
    db_session.add_all([prof, course])
    db_session.flush()

    assert load_grades_to_db([_row()], db_session) == 1

    assert db_session.query(Professor).count() == 1
    assert db_session.query(Course).count() == 1
    grade = db_session.query(GradeDistribution).one()
    assert (grade.professor_id, grade.course_id) == (prof.id, course.id)


def test_load_skips_duplicate_rows_within_one_batch(db_session):
    rows = [_row(), _row(), _row(instructor="ROE R")]
    assert load_grades_to_db(rows, db_session) == 2
    assert db_session.query(GradeDistribution).count() == 2
    assert db_session.query(Professor).count() == 2
    assert db_session.query(Course).count() == 1


def test_reload_query_count_does_not_grow_with_rows(db_session):
    """The quarterly job reloads the whole ~100k-row CSV over the network, so
    rows that are already loaded must not cost a round trip each."""
    rows = [_row(year=2000 + i) for i in range(30)]
    load_grades_to_db(rows, db_session)

    statements = []

    def record(conn, cursor, statement, *args):
        statements.append(statement)

    conn = db_session.connection()
    event.listen(conn, "before_cursor_execute", record)
    try:
        assert load_grades_to_db(rows, db_session) == 0
    finally:
        event.remove(conn, "before_cursor_execute", record)

    assert len(statements) < 10, statements

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


def _history(session, name, dept, rows):
    """An existing professor with grade rows loaded under their full name."""
    prof = Professor(name_nexus=name, department=dept)
    session.add(prof)
    session.flush()
    load_grades_to_db([{**r, "instructor": name} for r in rows], session)
    return prof


def test_abbreviated_name_reuses_the_full_name_professor(db_session):
    """FAVERTY P / FAVERTY P W: the 2026 CSV re-sent history under a shorter
    name, and the exact-name match created a duplicate professor with copies
    of the full-name row's grades (2026-09-28, ids 101039-101075)."""
    history = [_row(code="ED101", year=2010, dept="ED"), _row(code="ED102", year=2011, dept="ED")]
    full = _history(db_session, "FAVERTY P W", "ED", history)

    resent = [{**r, "instructor": "FAVERTY P"} for r in history]
    new_quarter = _row(instructor="FAVERTY P", code="ED101", year=2026, dept="ED")
    assert load_grades_to_db(resent + [new_quarter], db_session) == 1

    assert db_session.query(Professor).count() == 1
    grades = db_session.query(GradeDistribution).all()
    assert len(grades) == 3
    assert {g.professor_id for g in grades} == {full.id}


def test_abbreviated_name_matching_two_full_names_creates_a_professor(db_session):
    """WOODS M could be WOODS M J or WOODS M P, so it stays its own professor."""
    _history(db_session, "WOODS M J", "ED", [_row(code="ED321", year=2022, dept="ED")])
    _history(db_session, "WOODS M P", "ED", [_row(code="ED111", year=2023, dept="ED")])

    assert load_grades_to_db([_row(instructor="WOODS M", code="ED321", year=2020, dept="ED")], db_session) == 1

    woods_m = db_session.query(Professor).filter_by(name_nexus="WOODS M").one()
    grade = db_session.query(GradeDistribution).filter_by(year=2020).one()
    assert grade.professor_id == woods_m.id


def test_abbreviated_name_in_another_department_creates_a_professor(db_session):
    _history(db_session, "FAVERTY P W", "ED", [_row(code="ED101", year=2010, dept="ED")])

    load_grades_to_db([_row(instructor="FAVERTY P", code="MATH3A", year=2026, dept="MATH")], db_session)

    assert db_session.query(Professor).filter_by(name_nexus="FAVERTY P").count() == 1


def test_abbreviated_name_with_a_different_initial_creates_a_professor(db_session):
    _history(db_session, "TAGUE C L", "ESM", [_row(code="ESM100", year=2019, dept="ESM")])

    load_grades_to_db([_row(instructor="TAGUE D", code="ESM100", year=2026, dept="ESM")], db_session)

    assert db_session.query(Professor).filter_by(name_nexus="TAGUE D").count() == 1


def test_abbreviated_name_with_conflicting_grades_creates_a_professor(db_session):
    """RAVEN M / RAVEN M A: a second MCDB 126BL row for Winter 2015 with other
    numbers is another section (or instructor), not a re-sent copy. Resolving
    it would drop those students, so, like pass 4, it is left unmerged."""
    full = _history(db_session, "RAVEN M A", "MCDB", [_row(code="MCDB126BL", year=2015, dept="MCDB")])
    other_section = {**_row(instructor="RAVEN M", code="MCDB126BL", year=2015, dept="MCDB"), "a": 9}

    assert load_grades_to_db([other_section], db_session) == 1

    raven_m = db_session.query(Professor).filter_by(name_nexus="RAVEN M").one()
    assert raven_m.id != full.id
    assert db_session.query(GradeDistribution).count() == 2


def test_duplicate_full_name_rows_count_as_one_candidate(db_session):
    """Two KOTH M K rows are one name; the grades go to the oldest, as an exact match would."""
    oldest = _history(db_session, "KOTH M K", "ART", [_row(code="ART10", year=2018, dept="ART")])
    db_session.add(Professor(name_nexus="KOTH M K", department="ART"))
    db_session.flush()

    load_grades_to_db([_row(instructor="KOTH M", code="ART18", year=2019, dept="ART")], db_session)

    assert db_session.query(Professor).filter_by(name_nexus="KOTH M").count() == 0
    grade = db_session.query(GradeDistribution).filter_by(year=2019).one()
    assert grade.professor_id == oldest.id


def test_resolving_abbreviated_names_does_not_cost_a_query_per_row(db_session):
    history = [_row(instructor="FAVERTY P W", code="ED101", year=2000 + i, dept="ED") for i in range(30)]
    load_grades_to_db(history, db_session)
    resent = [{**r, "instructor": "FAVERTY P"} for r in history]

    statements = []

    def record(conn, cursor, statement, *args):
        statements.append(statement)

    conn = db_session.connection()
    event.listen(conn, "before_cursor_execute", record)
    try:
        assert load_grades_to_db(resent, db_session) == 0
    finally:
        event.remove(conn, "before_cursor_execute", record)

    assert len(statements) < 10, statements
    assert db_session.query(Professor).count() == 1

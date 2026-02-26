from db.models import Professor, Course, GradeDistribution

GRADE_FIELDS = [
    "a_plus", "a", "a_minus", "b_plus", "b", "b_minus",
    "c_plus", "c", "c_minus", "d_plus", "d", "d_minus", "f",
]


def _get_or_create_professor(session, name_nexus: str, department: str) -> Professor:
    prof = session.query(Professor).filter_by(name_nexus=name_nexus).first()
    if prof is None:
        prof = Professor(name_nexus=name_nexus, department=department)
        session.add(prof)
        session.flush()
    return prof


def _get_or_create_course(session, code: str, department: str) -> Course:
    course = session.query(Course).filter_by(code=code).first()
    if course is None:
        course = Course(code=code, department=department)
        session.add(course)
        session.flush()
    return course


def load_grades_to_db(rows: list[dict], session) -> int:
    """Load parsed grade rows into the database. Returns count of new rows inserted."""
    inserted = 0
    for row in rows:
        prof = _get_or_create_professor(session, row["instructor"], row.get("department", ""))
        course = _get_or_create_course(session, row["course_code"], row.get("department", ""))

        # Check for existing record (idempotent)
        existing = session.query(GradeDistribution).filter_by(
            professor_id=prof.id,
            course_id=course.id,
            quarter=row["quarter"],
            year=row["year"],
        ).first()
        if existing:
            continue

        grade = GradeDistribution(
            professor_id=prof.id,
            course_id=course.id,
            quarter=row["quarter"],
            year=row["year"],
            avg_gpa=row.get("avg_gpa", 0.0),
            **{f: row.get(f, 0) for f in GRADE_FIELDS},
        )
        session.add(grade)
        inserted += 1

    session.commit()
    return inserted

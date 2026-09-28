from db.models import Professor, Course, GradeDistribution

GRADE_FIELDS = [
    "a_plus", "a", "a_minus", "b_plus", "b", "b_minus",
    "c_plus", "c", "c_minus", "d_plus", "d", "d_minus", "f",
]


def load_grades_to_db(rows: list[dict], session) -> int:
    """Load parsed grade rows into the database. Returns count of new rows inserted.

    Idempotent: a (professor, course, quarter, year) already on record is
    skipped, so reloading the full Daily Nexus CSV only adds the new quarters.
    Professors are matched on name_nexus and courses on code, creating either
    when missing.

    Existing professors, courses and grade keys are read up front in three
    queries instead of three per row: the quarterly job reloads the whole
    ~100k-row CSV against a remote database, where per-row lookups meant
    hundreds of thousands of round trips.
    """
    prof_ids: dict[str, int] = {}
    for prof_id, name in (
        session.query(Professor.id, Professor.name_nexus)
        .filter(Professor.name_nexus.isnot(None))
        .order_by(Professor.id)
    ):
        prof_ids.setdefault(name, prof_id)  # oldest row wins, like the schedule sync

    course_ids: dict[str, int] = dict(session.query(Course.code, Course.id))

    seen = {
        tuple(key)
        for key in session.query(
            GradeDistribution.professor_id,
            GradeDistribution.course_id,
            GradeDistribution.quarter,
            GradeDistribution.year,
        )
    }

    inserted = 0
    for row in rows:
        name = row["instructor"]
        department = row.get("department", "")
        if name not in prof_ids:
            prof = Professor(name_nexus=name, department=department)
            session.add(prof)
            session.flush()
            prof_ids[name] = prof.id

        code = row["course_code"]
        if code not in course_ids:
            course = Course(code=code, department=department)
            session.add(course)
            session.flush()
            course_ids[code] = course.id

        key = (prof_ids[name], course_ids[code], row["quarter"], int(row["year"]))
        if key in seen:
            continue
        seen.add(key)

        session.add(GradeDistribution(
            professor_id=key[0],
            course_id=key[1],
            quarter=key[2],
            year=key[3],
            avg_gpa=row.get("avg_gpa", 0.0),
            **{f: row.get(f, 0) for f in GRADE_FIELDS},
        ))
        inserted += 1

    session.commit()
    return inserted

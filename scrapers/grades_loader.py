import logging
from collections import defaultdict

from db.models import Professor, Course, GradeDistribution
from etl.name_utils import find_duplicate_pairs

logger = logging.getLogger(__name__)

GRADE_FIELDS = [
    "a_plus", "a", "a_minus", "b_plus", "b", "b_minus",
    "c_plus", "c", "c_minus", "d_plus", "d", "d_minus", "f",
]


def _same_record(stored: GradeDistribution, row: dict) -> bool:
    """True when a CSV row carries exactly the numbers of a stored grade row."""
    if any(getattr(stored, f) != row.get(f, 0) for f in GRADE_FIELDS):
        return False
    return stored.avg_gpa == row.get("avg_gpa", 0.0)


def _resolve_abbreviated_names(
    rows: list[dict],
    session,
    prof_ids: dict[str, int],
    existing: list[dict],
    course_ids: dict[str, int],
    placeholders: frozenset[str] = frozenset(),
) -> dict[str, int]:
    """Map new abbreviated instructor names onto the existing professor they abbreviate.

    The Daily Nexus CSV sometimes re-publishes an instructor's history under a
    shorter name: the 2026 export labels rows "FAVERTY P" that earlier exports
    labelled "FAVERTY P W". An exact name match misses those, so the loader
    created a second professor and, because the new id made every
    (professor, course, quarter, year) key new, copied the history onto it.

    This applies pass 4's rule (etl.enhanced_matcher._pass4_deduplication)
    before the load instead of after it. A name with no exact match that is
    "LAST F" resolves to the one full name in the same department whose given
    name starts with F (etl.name_utils.find_duplicate_pairs). It is left alone,
    and created as a new professor as before, when:
      - several full names in the department fit ("WOODS M" with "WOODS M J"
        and "WOODS M P"), since the grades could belong to either;
      - one of its rows has different numbers from the candidate's row for the
        same course, quarter and year, which means two instructors or two
        sections. Pass 4 refuses to merge those too.
    Several rows with the same full name count as one candidate: the grades go
    to its oldest row, as they would for an exact match.

    ``placeholders`` are names whose exact match holds no grades and no RMP
    identity: rows the schedule sync created for a UCSB instructor it couldn't
    match. They go through the same rule, so the outcome doesn't depend on
    whether the sync saw the name first. Without this, the sync's "SCHMITT R"
    (ESM) took the CSV's "SCHMITT R" rows by exact match and got a copy of the
    grades already stored under "SCHMITT R J" (ENV). When the rule leaves a
    placeholder alone, it keeps its sync-created row instead of getting a new one.

    Only the name's first row's department is used, because that is the
    department the loader would create the professor with.
    """
    departments: dict[str, str] = {}
    for row in rows:
        if row["instructor"] not in prof_ids or row["instructor"] in placeholders:
            departments.setdefault(row["instructor"], row.get("department") or "")
    if not departments:
        return {}

    def fallback(name: str) -> str:
        if name in placeholders:
            return f"keeping its sync-created professor id={prof_ids[name]}"
        return "creating a new professor"

    incoming = [
        {"id": None, "name": name, "department": dept, "incoming": True}
        for name, dept in departments.items()
    ]
    candidates: dict[str, set[str]] = defaultdict(set)
    for abbr, full in find_duplicate_pairs(existing + incoming):
        if abbr.get("incoming") and not full.get("incoming"):
            candidates[abbr["name"]].add(full["name"])

    unique = {}
    for name, fulls in sorted(candidates.items()):
        if len(fulls) == 1:
            unique[name] = prof_ids[next(iter(fulls))]
        else:
            logger.warning(
                "Grades load: %r (%s) matches %d full names (%s); %s",
                name, departments[name], len(fulls), ", ".join(sorted(fulls)), fallback(name),
            )
    if not unique:
        return {}

    stored: dict[tuple, list[GradeDistribution]] = defaultdict(list)
    for grade in session.query(GradeDistribution).filter(
        GradeDistribution.professor_id.in_(set(unique.values()))
    ):
        stored[(grade.professor_id, grade.course_id, grade.quarter, grade.year)].append(grade)

    conflicts = set()
    for row in rows:
        name = row["instructor"]
        if name not in unique or name in conflicts:
            continue
        key = (unique[name], course_ids.get(row["course_code"]), row["quarter"], int(row["year"]))
        matches = stored.get(key)
        if matches and not any(_same_record(m, row) for m in matches):
            conflicts.add(name)
            logger.warning(
                "Grades load: %r has different grades from professor id=%d for %s %s %s; %s",
                name, unique[name], row["course_code"], row["quarter"], row["year"], fallback(name),
            )

    resolved = {name: prof_id for name, prof_id in unique.items() if name not in conflicts}
    for name, prof_id in resolved.items():
        logger.info(
            "Grades load: resolved %r (%s) to professor id=%d", name, departments[name], prof_id
        )
    return resolved


def load_grades_to_db(rows: list[dict], session) -> int:
    """Load parsed grade rows into the database. Returns count of new rows inserted.

    Idempotent: a (professor, course, quarter, year) already on record is
    skipped, so reloading the full Daily Nexus CSV only adds the new quarters.
    Professors are matched on name_nexus and courses on code, creating either
    when missing. A new abbreviated name that belongs to exactly one existing
    professor is matched to that professor instead, and so is one whose exact
    match is a sync-created row with no grades (see _resolve_abbreviated_names).

    Existing professors, courses and grade keys are read up front in three
    queries instead of three per row: the quarterly job reloads the whole
    ~100k-row CSV against a remote database, where per-row lookups meant
    hundreds of thousands of round trips. Resolving abbreviated names adds at
    most one more.
    """
    prof_ids: dict[str, int] = {}
    existing: list[dict] = []
    has_rmp: set[int] = set()
    for prof_id, name, department, rmp_id, name_rmp in (
        session.query(
            Professor.id, Professor.name_nexus, Professor.department,
            Professor.rmp_id, Professor.name_rmp,
        )
        .filter(Professor.name_nexus.isnot(None))
        .order_by(Professor.id)
    ):
        prof_ids.setdefault(name, prof_id)  # oldest row wins, like the schedule sync
        existing.append({"id": prof_id, "name": name, "department": department or ""})
        if rmp_id is not None or name_rmp is not None:
            has_rmp.add(prof_id)

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

    # Names whose rows hold no grades and no RMP identity: what the schedule
    # sync creates for an instructor it can't match.
    graded = {key[0] for key in seen} | has_rmp
    with_data = {p["name"] for p in existing if p["id"] in graded}
    placeholders = frozenset(p["name"] for p in existing if p["name"] not in with_data)

    resolved = _resolve_abbreviated_names(
        rows, session, prof_ids, existing, course_ids, placeholders
    )
    prof_ids.update(resolved)

    inserted = 0
    created = 0
    for row in rows:
        name = row["instructor"]
        department = row.get("department", "")
        if name not in prof_ids:
            prof = Professor(name_nexus=name, department=department)
            session.add(prof)
            session.flush()
            prof_ids[name] = prof.id
            created += 1

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
    logger.info(
        "Grades load: %d rows inserted, %d professors created, %d abbreviated names "
        "resolved to existing professors",
        inserted, created, len(resolved),
    )
    return inserted

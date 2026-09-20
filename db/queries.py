from collections import Counter
from datetime import datetime

from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from db.models import Professor, Course, GradeDistribution, RmpRating, RmpComment, ScheduledSection
from etl.name_matcher import is_confident_match

MONTH_NAMES = [
    "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

# Chronological rank of each quarter within a calendar year. The `quarter`
# column is text, so ordering by it in SQL sorts alphabetically (Fall, Spring,
# Summer, Winter) rather than by time. Matches the quarter-code convention used
# in api/routers/courses.py: Winter=1, Spring=2, Summer=3, Fall=4.
QUARTER_ORDER: dict[str, int] = {"Winter": 1, "Spring": 2, "Summer": 3, "Fall": 4}

# ---------------------------------------------------------------------------
# Tag Vocabulary — maps raw keyword substrings (lowercase) to curated tags
# ---------------------------------------------------------------------------
# Categories: Grading, Teaching, Workload, Exams, Personality, Logistics, Other

TAG_VOCABULARY: dict[str, str] = {
    # Grading
    "easy": "Easy Grader",
    "lenient": "Easy Grader",
    "generous": "Easy Grader",
    "tough grad": "Tough Grader",
    "strict grad": "Tough Grader",
    "hard grad": "Tough Grader",
    # Teaching
    "engaging": "Engaging",
    "interesting": "Engaging",
    "fun": "Engaging",
    "entertaining": "Engaging",
    "boring": "Dry Lectures",
    "dry": "Dry Lectures",
    "dull": "Dry Lectures",
    "monotone": "Dry Lectures",
    "clear": "Clear Explanations",
    "explains well": "Clear Explanations",
    "understandable": "Clear Explanations",
    # Workload
    "heavy": "Heavy Workload",
    "lot of work": "Heavy Workload",
    "tons of homework": "Heavy Workload",
    "too much": "Heavy Workload",
    "light": "Light Workload",
    "easy workload": "Light Workload",
    "manageable": "Light Workload",
    "not much work": "Light Workload",
    # Exams
    "hard exam": "Tough Exams",
    "tough exam": "Tough Exams",
    "difficult test": "Tough Exams",
    "tricky": "Tough Exams",
    "fair exam": "Fair Tests",
    "fair test": "Fair Tests",
    "reasonable exam": "Fair Tests",
    # Personality
    "helpful": "Helpful",
    "available": "Helpful",
    "office hours": "Helpful",
    "approachable": "Helpful",
    "caring": "Caring",
    "kind": "Caring",
    "understanding": "Caring",
    "supportive": "Caring",
    "intimidating": "Intimidating",
    "scary": "Intimidating",
    "mean": "Intimidating",
    "rude": "Intimidating",
    # Logistics
    "attendance": "Attendance Mandatory",
    "mandatory": "Attendance Mandatory",
    "roll call": "Attendance Mandatory",
    "extra credit": "Extra Credit",
    "bonus": "Extra Credit",
    # Other
    "take again": "Would Take Again",
    "recommend": "Would Take Again",
}


def map_keywords_to_tags(
    raw_keywords: list[str], min_count: int = 3
) -> list[dict]:
    """Map a flat list of raw keywords to curated tags with frequency filtering.

    Each entry in *raw_keywords* represents one keyword from one comment.
    Per-comment deduplication (so one comment with both "easy" and "lenient"
    only counts once for "Easy Grader") must be done **before** calling this
    function -- see get_professors_for_course().

    Returns at most 6 tags sorted by count descending, each with count >= min_count.
    """
    tag_counts: Counter[str] = Counter()
    for kw in raw_keywords:
        kw_lower = kw.lower()
        for substring, tag_name in TAG_VOCABULARY.items():
            if substring in kw_lower:
                tag_counts[tag_name] += 1
                break  # first match wins per keyword

    # Filter by threshold, sort descending, cap at 6
    filtered = [
        {"name": name, "count": count}
        for name, count in tag_counts.most_common()
        if count >= min_count
    ]
    return filtered[:6]


def get_departments(session: Session) -> list[str]:
    """Get all distinct department names, sorted."""
    rows = session.query(Course.department).distinct().order_by(Course.department).all()
    return [r[0] for r in rows if r[0]]


def search_courses(session: Session, query: str, department: str | None = None) -> list[dict]:
    """Search courses by code or title fragment, optionally filtered by department.

    Course codes are stored with all whitespace removed (see
    scrapers/grades_ingester.normalize_course_code), so the code half of the
    search collapses whitespace in the query too — otherwise "CS 16", the way
    the university writes it, can never match the stored "CS16". Titles do
    contain spaces, so the title half matches the query as typed.
    """
    code_query = "".join(query.split())
    title_query = " ".join(query.split())

    q = session.query(Course)
    # An empty query means "browse everything" (optionally within a department),
    # so only constrain by text when the caller actually supplied some.
    if code_query:
        q = q.filter(
            or_(
                Course.code.ilike(f"%{code_query}%"),
                Course.title.ilike(f"%{title_query}%"),
            )
        )
    if department:
        q = q.filter(Course.department == department)
    courses = q.order_by(Course.code).limit(20).all()
    return [{"id": c.id, "code": c.code, "title": c.title, "department": c.department} for c in courses]


def get_professors_for_course(session: Session, course_id: int, min_year: int | None = None) -> list[dict]:
    """Get all professors who have taught a course, with their stats. 3 queries max."""

    cutoff_year = datetime.now().year - 3

    # Subquery: latest RMP rating per professor
    latest_rating_sq = (
        session.query(
            RmpRating.professor_id,
            func.max(RmpRating.id).label("latest_rating_id"),  # assumes max(id) == most recently fetched; valid for sequential ETL inserts
        )
        .group_by(RmpRating.professor_id)
        .subquery("latest_rating")
    )

    # Subquery: sentiment stats per RMP rating
    sentiment_sq = (
        session.query(
            RmpComment.rmp_rating_id,
            func.avg(RmpComment.sentiment_score).label("avg_sentiment"),
        )
        .filter(RmpComment.sentiment_score.isnot(None))
        .group_by(RmpComment.rmp_rating_id)
        .subquery("sentiment")
    )

    # Subquery: count distinct (quarter, year) pairs in recent years per professor
    recent_grades_sq = (
        session.query(
            GradeDistribution.professor_id,
            GradeDistribution.quarter,
            GradeDistribution.year,
        )
        .filter(
            GradeDistribution.course_id == course_id,
            GradeDistribution.year >= cutoff_year,
        )
        .group_by(GradeDistribution.professor_id, GradeDistribution.quarter, GradeDistribution.year)
        .subquery("recent_distinct")
    )
    # Wrap to count the distinct quarter-year pairs per professor
    active_teaching_sq = (
        session.query(
            recent_grades_sq.c.professor_id,
            func.count().label("distinct_recent_quarters"),
        )
        .group_by(recent_grades_sq.c.professor_id)
        .subquery("active_teaching")
    )

    # Main query: professors + grade stats + RMP data + sentiment + active teaching
    q = (
        session.query(
            Professor,
            func.avg(GradeDistribution.avg_gpa).label("mean_gpa"),
            func.stddev(GradeDistribution.avg_gpa).label("std_gpa"),
            func.count(GradeDistribution.id).label("quarters_taught"),
            RmpRating,
            sentiment_sq.c.avg_sentiment,
            active_teaching_sq.c.distinct_recent_quarters,
        )
        .join(GradeDistribution, GradeDistribution.professor_id == Professor.id)
        .filter(GradeDistribution.course_id == course_id)
        .outerjoin(latest_rating_sq, latest_rating_sq.c.professor_id == Professor.id)
        .outerjoin(RmpRating, RmpRating.id == latest_rating_sq.c.latest_rating_id)
        .outerjoin(sentiment_sq, sentiment_sq.c.rmp_rating_id == RmpRating.id)
        .outerjoin(active_teaching_sq, active_teaching_sq.c.professor_id == Professor.id)
    )
    if min_year is not None:
        q = q.filter(GradeDistribution.year >= min_year)
    results = q.group_by(
        Professor.id, RmpRating.id, sentiment_sq.c.avg_sentiment,
        active_teaching_sq.c.distinct_recent_quarters,
    ).all()

    # 2nd query: keywords grouped by rating_id (not N+1)
    # Collect per-comment keyword lists so we can deduplicate tags within a comment.
    rating_ids = [row[4].id for row in results if row[4] is not None]
    # Map: rating_id -> list of per-comment keyword lists
    comments_kw_map: dict[int, list[list[str]]] = {}
    if rating_ids:
        keyword_rows = (
            session.query(RmpComment.rmp_rating_id, RmpComment.keywords)
            .filter(RmpComment.rmp_rating_id.in_(rating_ids), RmpComment.keywords.isnot(None))
            .all()
        )
        for rating_id, kw in keyword_rows:
            if isinstance(kw, list):
                comments_kw_map.setdefault(rating_id, []).append(kw)

    # 3rd query: recent quarters per professor for this course
    prof_ids = [row[0].id for row in results]
    quarters_map: dict[int, list[str]] = {}
    if prof_ids:
        quarter_order = QUARTER_ORDER
        quarter_rows = (
            session.query(
                GradeDistribution.professor_id,
                GradeDistribution.quarter,
                GradeDistribution.year,
            )
            .filter(
                GradeDistribution.course_id == course_id,
                GradeDistribution.year >= cutoff_year,
                GradeDistribution.professor_id.in_(prof_ids),
            )
            .distinct()
            .all()
        )
        raw_map: dict[int, list[tuple[str, int]]] = {}
        for pid, q_name, y in quarter_rows:
            raw_map.setdefault(pid, []).append((q_name, y))
        for pid in raw_map:
            raw_map[pid].sort(key=lambda x: (x[1], quarter_order.get(x[0], 0)), reverse=True)
            quarters_map[pid] = [f"{q_name} {y}" for q_name, y in raw_map[pid]]

    professors = []
    for prof, mean_gpa, std_gpa, quarters_taught, rmp, avg_sentiment, active_count in results:
        # DATA-1: only surface RMP data when the name match is confident enough
        # to publish as fact. Weak or missing confidence is treated as unmatched
        # so students never see another person's reviews attributed as truth.
        confident = is_confident_match(prof.match_confidence)
        trusted_rmp = rmp if confident else None

        # Per-comment deduplication: for each comment's keyword list, map to tags
        # and deduplicate so one comment only counts once per tag.
        comment_kw_lists = comments_kw_map.get(trusted_rmp.id, []) if trusted_rmp else []
        deduped_keywords: list[str] = []
        for comment_keywords in comment_kw_lists:
            # Map this comment's raw keywords to tag names, deduplicate within comment
            mapped_tags: set[str] = set()
            for kw in comment_keywords:
                kw_lower = kw.lower()
                for substring, tag_name in TAG_VOCABULARY.items():
                    if substring in kw_lower:
                        mapped_tags.add(tag_name)
                        break
            # Each unique tag from this comment contributes one "vote"
            # We re-use the tag name as the keyword so map_keywords_to_tags can count
            deduped_keywords.extend(mapped_tags)

        tags = map_keywords_to_tags(deduped_keywords, min_count=3) if trusted_rmp else []

        distinct_recent = active_count if active_count else 0
        is_active = distinct_recent >= 3
        # Prefer the Nexus roster name when the RMP link is untrusted — otherwise
        # a weak match would still display the wrong person's name.
        display_name = (
            (prof.name_rmp if confident and prof.name_rmp else None)
            or prof.name_nexus
            or "Unknown"
        )
        professors.append({
            "id": prof.id,
            "name": display_name,
            "department": prof.department,
            "mean_gpa": round(float(mean_gpa), 2) if mean_gpa is not None else None,
            "std_gpa": round(float(std_gpa), 2) if std_gpa is not None else None,
            "quarters_taught": quarters_taught,
            "rmp_quality": trusted_rmp.overall_quality if trusted_rmp else None,
            "rmp_difficulty": trusted_rmp.difficulty if trusted_rmp else None,
            "rmp_would_take_again": trusted_rmp.would_take_again_pct if trusted_rmp else None,
            "rmp_num_ratings": trusted_rmp.num_ratings if trusted_rmp else None,
            "avg_sentiment": (
                round(float(avg_sentiment), 2)
                if trusted_rmp is not None and avg_sentiment is not None
                else None
            ),
            "tags": tags,
            "match_confidence": prof.match_confidence if confident else None,
            "is_active_teacher": is_active,
            "recent_quarters": quarters_map.get(prof.id, []),
        })

    return professors


def get_grade_history(session: Session, professor_id: int, course_id: int) -> list[dict]:
    """Get quarter-by-quarter grade history for a professor+course, oldest first.

    Ordered chronologically by (year, quarter rank). Ordering by the raw
    `quarter` text column sorts alphabetically — Fall, Spring, Summer, Winter —
    which puts Fall before Spring within the same year. Consumers depend on
    true chronological order: GradeChart treats the last element as the most
    recent quarter, and GpaTrendChart plots the array order onto the x-axis.
    """
    grades = (
        session.query(GradeDistribution)
        .filter_by(professor_id=professor_id, course_id=course_id)
        .all()
    )
    grades.sort(key=lambda g: (g.year, QUARTER_ORDER.get(g.quarter, 0)))
    return [
        {
            "quarter": f"{g.quarter} {g.year}",
            "avg_gpa": g.avg_gpa,
            "a_plus": g.a_plus, "a": g.a, "a_minus": g.a_minus,
            "b_plus": g.b_plus, "b": g.b, "b_minus": g.b_minus,
            "c_plus": g.c_plus, "c": g.c, "c_minus": g.c_minus,
            "d_plus": g.d_plus, "d": g.d, "d_minus": g.d_minus,
            "f": g.f,
        }
        for g in grades
    ]


def get_comments_for_professor(session: Session, professor_id: int, limit: int = 5) -> list[dict]:
    """Fetch the most recent RMP comments for a professor.

    Returns an empty list when the professor's RMP link is below the publish
    confidence threshold (DATA-1) — otherwise a weak match would still expose
    another person's reviews via the comments endpoint.
    """
    prof = session.get(Professor, professor_id)
    if prof is None or not is_confident_match(prof.match_confidence):
        return []

    comments = (
        session.query(RmpComment)
        .join(RmpRating, RmpComment.rmp_rating_id == RmpRating.id)
        .filter(RmpRating.professor_id == professor_id)
        .order_by(RmpComment.created_at.desc().nullslast())
        .limit(limit)
        .all()
    )
    results = []
    for c in comments:
        if c.created_at:
            formatted_date = f"{MONTH_NAMES[c.created_at.month]} {c.created_at.year}"
        else:
            formatted_date = None
        results.append({
            "text": c.comment_text,
            "sentiment_score": c.sentiment_score,
            "keywords": c.keywords,
            "created_at": formatted_date,
        })
    return results


def get_scheduled_sections(
    session: Session,
    course_id: int,
    professor_ids: list[int],
    quarter_code: str | None = None,
) -> dict[int, list[dict]]:
    """Get scheduled sections grouped by professor_id.

    Parameters
    ----------
    session : Session
        SQLAlchemy session.
    course_id : int
        The course to look up sections for.
    professor_ids : list[int]
        Professor IDs to filter by.
    quarter_code : str, optional
        If provided, filter to a specific quarter. Otherwise returns all.

    Returns
    -------
    dict[int, list[dict]]
        Mapping from professor_id to list of section dicts.
    """
    if not professor_ids:
        return {}

    q = (
        session.query(ScheduledSection)
        .filter(
            ScheduledSection.course_id == course_id,
            ScheduledSection.professor_id.in_(professor_ids),
            ScheduledSection.section_cancelled == False,
        )
    )
    if quarter_code:
        q = q.filter(ScheduledSection.quarter_code == quarter_code)

    sections = q.order_by(ScheduledSection.quarter_code.desc(), ScheduledSection.enroll_code).all()

    result: dict[int, list[dict]] = {}
    for s in sections:
        entry = {
            "quarter_code": s.quarter_code,
            "quarter_name": s.quarter_name,
            "enroll_code": s.enroll_code,
            "instructor_name_raw": s.instructor_name_raw,
            "days": s.days,
            "begin_time": s.begin_time,
            "end_time": s.end_time,
            "building": s.building,
            "room": s.room,
            "enrolled": s.enrolled,
            "max_enroll": s.max_enroll,
        }
        result.setdefault(s.professor_id, []).append(entry)

    return result


def get_all_course_sections(
    session: Session,
    course_id: int,
    quarter_codes: list[str],
) -> list[dict]:
    """Get all scheduled sections for a course, filtered to named instructors with meeting times.

    Returns a flat list of section dicts sorted by quarter (desc) then enroll code.
    """
    sections = (
        session.query(ScheduledSection)
        .filter(
            ScheduledSection.course_id == course_id,
            ScheduledSection.quarter_code.in_(quarter_codes),
            ScheduledSection.section_cancelled == False,
            ScheduledSection.instructor_name_raw.isnot(None),
            ScheduledSection.instructor_name_raw != "",
        )
        .filter(
            # Must have at least days or begin_time
            (ScheduledSection.days.isnot(None)) | (ScheduledSection.begin_time.isnot(None))
        )
        .order_by(ScheduledSection.quarter_code.desc(), ScheduledSection.enroll_code)
        .all()
    )

    return [
        {
            "quarter_code": s.quarter_code,
            "quarter_name": s.quarter_name,
            "enroll_code": s.enroll_code,
            "instructor_name_raw": s.instructor_name_raw,
            "days": s.days,
            "begin_time": s.begin_time,
            "end_time": s.end_time,
            "building": s.building,
            "room": s.room,
            "enrolled": s.enrolled,
            "max_enroll": s.max_enroll,
        }
        for s in sections
    ]


def get_data_freshness(session: Session) -> dict:
    """Return the newest grade term and the latest schedule fetch time."""
    latest_year = session.query(func.max(GradeDistribution.year)).scalar()
    latest_quarter = None
    if latest_year is not None:
        quarters = [
            row[0]
            for row in (
                session.query(GradeDistribution.quarter)
                .filter(GradeDistribution.year == latest_year)
                .distinct()
                .all()
            )
            if row[0]
        ]
        if quarters:
            latest_quarter = max(quarters, key=lambda q: QUARTER_ORDER.get(q, 0))
    latest_fetch = session.query(func.max(ScheduledSection.fetched_at)).scalar()
    return {
        "latest_grade_year": latest_year,
        "latest_grade_quarter": latest_quarter,
        "schedule_fetched_at": latest_fetch.isoformat() if latest_fetch else None,
    }

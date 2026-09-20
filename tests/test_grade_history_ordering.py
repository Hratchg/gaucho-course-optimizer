"""Regression tests for BUG-3 — grade history must be chronological.

The `quarter` column is text, so ordering by it in SQL sorts alphabetically
(Fall, Spring, Summer, Winter), which puts Fall 2020 before Spring 2020.
GradeChart treats the last element as "most recent" and GpaTrendChart plots
array order onto the x-axis, so both break when the order is alphabetical.
"""
from db.models import Professor, Course, GradeDistribution
from dashboard.queries import get_grade_history


def _seed(session, quarters):
    prof = Professor(name_nexus="ORDER TEST", department="MATH")
    course = Course(code="MATHORD", title="Ordering", department="MATH")
    session.add_all([prof, course])
    session.flush()

    session.add_all([
        GradeDistribution(
            professor_id=prof.id,
            course_id=course.id,
            quarter=quarter,
            year=year,
            avg_gpa=gpa,
        )
        for quarter, year, gpa in quarters
    ])
    session.flush()
    return prof, course


def test_quarters_within_a_year_are_chronological(db_session):
    """Winter → Spring → Summer → Fall, not the alphabetical Fall → Spring → Summer → Winter."""
    prof, course = _seed(db_session, [
        ("Fall", 2020, 3.4),
        ("Winter", 2020, 3.0),
        ("Summer", 2020, 3.3),
        ("Spring", 2020, 3.1),
    ])

    history = get_grade_history(db_session, prof.id, course.id)

    assert [h["quarter"] for h in history] == [
        "Winter 2020", "Spring 2020", "Summer 2020", "Fall 2020",
    ]


def test_years_sort_before_quarters(db_session):
    """Ordering is (year, quarter) — an earlier year always comes first."""
    prof, course = _seed(db_session, [
        ("Winter", 2021, 3.5),
        ("Fall", 2019, 3.0),
        ("Spring", 2020, 3.2),
    ])

    history = get_grade_history(db_session, prof.id, course.id)

    assert [h["quarter"] for h in history] == [
        "Fall 2019", "Spring 2020", "Winter 2021",
    ]


def test_last_element_is_most_recent(db_session):
    """GradeChart relies on the final element being the latest quarter."""
    prof, course = _seed(db_session, [
        ("Fall", 2022, 3.6),
        ("Winter", 2022, 3.1),
    ])

    history = get_grade_history(db_session, prof.id, course.id)

    assert history[-1]["quarter"] == "Fall 2022"
    assert history[-1]["avg_gpa"] == 3.6


def test_unknown_quarter_name_does_not_crash(db_session):
    """An unexpected quarter label sorts first rather than raising."""
    prof, course = _seed(db_session, [
        ("Fall", 2021, 3.4),
        ("Interim", 2021, 3.2),
    ])

    history = get_grade_history(db_session, prof.id, course.id)

    assert len(history) == 2
    assert history[-1]["quarter"] == "Fall 2021"

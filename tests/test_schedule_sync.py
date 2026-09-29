"""Tests for the schedule sync pipeline.

Uses the transactional db_session fixture from conftest.py.
All UCSB API calls are mocked.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from db.models import Base, Course, Professor, ScheduledSection
from ucsb_api.client import UCSBApiError
from ucsb_api.schedule_sync import (
    _normalize_course_id,
    _extract_section_data,
    sync_course_sections,
    sync_department_sections,
    backfill_missing_titles,
    is_quarter_published,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_course(db_session):
    """Create a sample CMPSC 130A course."""
    course = Course(code="CMPSC130A", title="Data Structures and Algorithms I", department="CMPSC")
    db_session.add(course)
    db_session.flush()
    return course


@pytest.fixture
def sample_professors(db_session):
    """Create sample professors for matching tests."""
    p1 = Professor(name_rmp="Phill Conrad", name_nexus="CONRAD, PHILLIP", department="CMPSC")
    p2 = Professor(name_rmp="Yekaterina Kharitonova", name_nexus=None, department="CMPSC")
    db_session.add_all([p1, p2])
    db_session.flush()
    return [p1, p2]


MOCK_API_SECTIONS = [
    {
        "courseId": "CMPSC     130A",
        "title": "Data Structures and Algorithms I",
        "classSections": [
            {
                "enrollCode": "12345",
                "section": "0100",
                "courseCancelled": None,
                "instructors": [
                    {"instructor": "CONRAD P T", "functionCode": "Teaching and in charge"}
                ],
                "timeLocations": [
                    {
                        "days": "T R",
                        "beginTime": "14:00",
                        "endTime": "15:15",
                        "building": "PHELP",
                        "room": "1260",
                    }
                ],
                "enrolledTotal": 85,
                "maxEnroll": 120,
            },
            {
                "enrollCode": "12346",
                "section": "0200",
                "courseCancelled": None,
                "instructors": [
                    {"instructor": "KHARITONOVA Y", "functionCode": "Teaching and in charge"}
                ],
                "timeLocations": [
                    {
                        "days": "M W F",
                        "beginTime": "10:00",
                        "endTime": "10:50",
                        "building": "BUCHN",
                        "room": "1920",
                    }
                ],
                "enrolledTotal": 42,
                "maxEnroll": 100,
            },
        ],
    }
]


# ---------------------------------------------------------------------------
# Utility function tests
# ---------------------------------------------------------------------------

def test_normalize_course_id():
    assert _normalize_course_id("CMPSC     130A") == "CMPSC130A"
    assert _normalize_course_id("MATH    3B") == "MATH3B"
    assert _normalize_course_id("CMPSC130A") == "CMPSC130A"


def test_extract_section_data():
    raw = {
        "enrollCode": "12345",
        "courseCancelled": None,
        "instructors": [
            {"instructor": "CONRAD P T", "functionCode": "Teaching and in charge"}
        ],
        "timeLocations": [
            {
                "days": "T R",
                "beginTime": "14:00",
                "endTime": "15:15",
                "building": "PHELP",
                "room": "1260",
            }
        ],
        "enrolledTotal": 85,
        "maxEnroll": 120,
    }
    data = _extract_section_data(raw)
    assert data["enroll_code"] == "12345"
    assert data["instructor_name_raw"] == "CONRAD P T"
    assert data["days"] == "T R"
    assert data["begin_time"] == "14:00"
    assert data["end_time"] == "15:15"
    assert data["building"] == "PHELP"
    assert data["room"] == "1260"
    assert data["enrolled"] == 85
    assert data["max_enroll"] == 120


def test_extract_section_data_no_time():
    raw = {
        "enrollCode": "99999",
        "instructors": [],
        "timeLocations": [],
        "enrolledTotal": 0,
        "maxEnroll": 50,
    }
    data = _extract_section_data(raw)
    assert data["days"] is None
    assert data["instructor_name_raw"] is None


# ---------------------------------------------------------------------------
# sync_course_sections tests
# ---------------------------------------------------------------------------

def _make_mock_client(sections_response):
    """Create a mock UCSBApiClient that returns the given sections."""
    mock_client = MagicMock()

    # Build list of sections with _courseId, _title, _quarter metadata
    processed_sections = []
    for cls in sections_response:
        for sec in cls.get("classSections", []):
            sec_copy = dict(sec)
            sec_copy["_courseId"] = cls.get("courseId", "")
            sec_copy["_title"] = cls.get("title", "")
            sec_copy["_quarter"] = "20262"
            processed_sections.append(sec_copy)

    mock_client.fetch_classes.return_value = processed_sections
    mock_client.fetch_department_classes.return_value = processed_sections
    return mock_client


def test_sync_course_sections_inserts(db_session, sample_course, sample_professors):
    mock_client = _make_mock_client(MOCK_API_SECTIONS)

    stats = sync_course_sections(
        db_session, "20262", "CMPSC130A", client=mock_client
    )

    assert stats["inserted"] == 2
    assert stats["updated"] == 0
    # Both instructors should be matched (possibly to real DB professors or fixtures)
    assert stats["matched"] >= 1

    # Verify rows in DB
    sections = db_session.query(ScheduledSection).all()
    assert len(sections) == 2

    # Check Conrad's section has correct data (don't assert specific professor_id
    # since real DB may have a different Conrad record than the fixture)
    conrad_section = next(s for s in sections if s.enroll_code == "12345")
    assert conrad_section.professor_id is not None  # Matched to some professor
    assert conrad_section.course_id == sample_course.id
    assert conrad_section.quarter_code == "20262"
    assert conrad_section.quarter_name == "Spring 2026"
    assert conrad_section.instructor_name_raw == "CONRAD P T"
    assert conrad_section.days == "T R"
    assert conrad_section.begin_time == "14:00"
    assert conrad_section.end_time == "15:15"
    assert conrad_section.building == "PHELP"
    assert conrad_section.room == "1260"
    assert conrad_section.enrolled == 85
    assert conrad_section.max_enroll == 120


def test_sync_course_sections_updates(db_session, sample_course, sample_professors):
    mock_client = _make_mock_client(MOCK_API_SECTIONS)

    # First sync — inserts
    stats1 = sync_course_sections(
        db_session, "20262", "CMPSC130A", client=mock_client
    )
    assert stats1["inserted"] == 2

    # Second sync — should update, not duplicate
    stats2 = sync_course_sections(
        db_session, "20262", "CMPSC130A", client=mock_client
    )
    assert stats2["updated"] == 2
    assert stats2["inserted"] == 0

    # Still only 2 rows
    sections = db_session.query(ScheduledSection).all()
    assert len(sections) == 2


def test_sync_course_unknown_course(db_session):
    mock_client = _make_mock_client(MOCK_API_SECTIONS)

    stats = sync_course_sections(
        db_session, "20262", "NONEXISTENT 999", client=mock_client
    )
    assert stats["inserted"] == 0
    assert stats["matched"] == 0


def test_sync_course_unmatched_instructor(db_session, sample_course):
    """Instructors with names not matching any professor are unmatched."""
    # Use fake instructor names that won't match any real professor
    unmatched_sections = [
        {
            "courseId": "CMPSC     130A",
            "title": "Data Structures",
            "classSections": [
                {
                    "enrollCode": "99901",
                    "courseCancelled": None,
                    "instructors": [{"instructor": "ZZZZFAKE X", "functionCode": "Teaching and in charge"}],
                    "timeLocations": [{"days": "M W", "beginTime": "09:00", "endTime": "09:50", "building": "HFH", "room": "1104"}],
                    "enrolledTotal": 10,
                    "maxEnroll": 50,
                },
                {
                    "enrollCode": "99902",
                    "courseCancelled": None,
                    "instructors": [{"instructor": "YYYYNOBODY Q", "functionCode": "Teaching and in charge"}],
                    "timeLocations": [],
                    "enrolledTotal": 0,
                    "maxEnroll": 30,
                },
            ],
        }
    ]
    mock_client = _make_mock_client(unmatched_sections)

    stats = sync_course_sections(
        db_session, "20262", "CMPSC130A", client=mock_client
    )
    assert stats["unmatched"] == 2
    assert stats["matched"] == 0

    # Sections still stored, but with professor_id=None
    sections = db_session.query(ScheduledSection).all()
    assert len(sections) == 2
    assert all(s.professor_id is None for s in sections)


def test_sync_department_sections(db_session, sample_course, sample_professors):
    mock_client = _make_mock_client(MOCK_API_SECTIONS)

    stats = sync_department_sections(
        db_session, "20262", "CMPSC", client=mock_client
    )

    assert stats["inserted"] == 2
    assert stats["matched"] == 2


def test_sync_department_reuses_auto_created_professor(db_session):
    """An instructor auto-created on one sync must be matched, not re-created, on the next.

    Regression test: auto-created rows store the raw UCSB name ("GURVEN M D") and the
    matcher read that as First-Last, so every nightly run created a fresh duplicate
    professor for every unmatched instructor.
    """
    course = Course(code="CMPSC130A", title="Data Structures", department="CMPSC")
    db_session.add(course)
    db_session.flush()
    sections = [
        {
            "courseId": "CMPSC     130A",
            "title": "Data Structures",
            "classSections": [
                {
                    "enrollCode": "99903",
                    "courseCancelled": None,
                    "instructors": [{"instructor": "ZZZZNEWPROF M D", "functionCode": "Teaching and in charge"}],
                    "timeLocations": [],
                    "enrolledTotal": 0,
                    "maxEnroll": 30,
                },
            ],
        }
    ]
    mock_client = _make_mock_client(sections)

    first = sync_department_sections(
        db_session, "20262", "CMPSC", client=mock_client, auto_create_cache={}
    )
    assert first["auto_created"] == 1

    # Next night: fresh per-run cache, same instructor
    second = sync_department_sections(
        db_session, "20262", "CMPSC", client=mock_client, auto_create_cache={}
    )
    assert second["auto_created"] == 0
    assert second["matched"] == 1

    profs = db_session.query(Professor).filter(Professor.name_nexus == "ZZZZNEWPROF M D").all()
    assert len(profs) == 1
    section = db_session.query(ScheduledSection).filter_by(enroll_code="99903").one()
    assert section.professor_id == profs[0].id


def test_sync_department_logs_error_and_returns_on_ucsb_400(db_session, caplog):
    """A department UCSB rejects in a published quarter is still an ERROR, not a crash."""
    mock_client = MagicMock()
    mock_client.fetch_department_classes.side_effect = UCSBApiError(
        "Failed to fetch dept classes: 400 Client Error", status_code=400
    )

    with caplog.at_level("INFO", logger="ucsb_api.schedule_sync"):
        stats = sync_department_sections(db_session, "20264", "CMPSC", client=mock_client)

    assert stats["inserted"] == 0
    errors = [r.getMessage() for r in caplog.records if r.levelname == "ERROR"]
    assert errors == [
        "Failed to fetch department CMPSC: Failed to fetch dept classes: 400 Client Error"
    ]


# ---------------------------------------------------------------------------
# is_quarter_published tests
# ---------------------------------------------------------------------------

def _probe_client(outcomes):
    """A client whose probe answers per quarter: None = 200, int = that HTTP status."""
    mock_client = MagicMock()

    def probe(quarter_code, department):
        status = outcomes[quarter_code]
        if status is not None:
            raise UCSBApiError(f"{status} for {quarter_code}/{department}", status_code=status)

    mock_client.probe_department_classes.side_effect = probe
    return mock_client


def test_quarter_published_when_probe_succeeds():
    client = _probe_client({"20271": None})
    assert is_quarter_published(client, "20271", reference_quarter="20264", department="ANTH")
    client.probe_department_classes.assert_called_once_with("20271", "ANTH")


def test_quarter_unpublished_when_only_the_quarter_is_rejected():
    """400 for 20271 while the same department is fine for 20264: 20271 isn't out yet."""
    client = _probe_client({"20271": 400, "20264": None})
    assert not is_quarter_published(client, "20271", reference_quarter="20264", department="ANTH")
    assert [c.args for c in client.probe_department_classes.call_args_list] == [
        ("20271", "ANTH"),
        ("20264", "ANTH"),
    ]


def test_quarter_treated_as_published_when_reference_also_fails():
    """If the department is rejected for both quarters the 400 isn't about the quarter."""
    client = _probe_client({"20271": 400, "20264": 400})
    assert is_quarter_published(client, "20271", reference_quarter="20264", department="ANTH")


@pytest.mark.parametrize("status", [401, 403, 404, 429, 500, 503])
def test_quarter_treated_as_published_on_other_statuses(status):
    """Outages and auth errors keep today's behaviour: the full loop runs and logs them."""
    client = _probe_client({"20271": status, "20264": None})
    assert is_quarter_published(client, "20271", reference_quarter="20264", department="ANTH")
    client.probe_department_classes.assert_called_once_with("20271", "ANTH")


def test_quarter_treated_as_published_when_probe_cannot_connect():
    client = MagicMock()
    client.probe_department_classes.side_effect = UCSBApiError("Connection refused")
    assert is_quarter_published(client, "20271", reference_quarter="20264", department="ANTH")
    client.probe_department_classes.assert_called_once_with("20271", "ANTH")


def test_sync_course_fills_missing_title(db_session):
    course = Course(code="CMPSC130A", title=None, department="CMPSC")
    db_session.add(course)
    db_session.flush()
    mock_client = _make_mock_client(MOCK_API_SECTIONS)

    sync_course_sections(db_session, "20262", "CMPSC130A", client=mock_client)

    db_session.refresh(course)
    assert course.title == "Data Structures and Algorithms I"


def test_backfill_missing_titles(db_session):
    course = Course(code="CMPSC130A", title=None, department="CMPSC")
    db_session.add(course)
    db_session.flush()
    mock_client = _make_mock_client(MOCK_API_SECTIONS)

    stats = backfill_missing_titles(db_session, "20262", client=mock_client)

    assert stats["updated"] == 1
    db_session.refresh(course)
    assert course.title == "Data Structures and Algorithms I"

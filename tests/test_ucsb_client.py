"""Tests for UCSB API client and instructor name matcher.

All API calls are mocked — no real HTTP requests during testing.
"""

import pytest
from unittest.mock import patch, MagicMock

from ucsb_api.client import (
    UCSBApiClient,
    UCSBApiError,
    get_next_quarter_code,
    quarter_code_to_name,
)
from ucsb_api.name_matcher import (
    parse_ucsb_instructor,
    match_instructor_to_professor,
    ParsedInstructor,
    _extract_professor_last_name,
    _extract_professor_first_initial,
)


# ---------------------------------------------------------------------------
# UCSBApiClient tests
# ---------------------------------------------------------------------------

MOCK_CLASSES_RESPONSE = [
    {
        "courseId": "CMPSC     130A",
        "title": "Data Structures and Algorithms I",
        "classSections": [
            {
                "enrollCode": "12345",
                "section": "0100",
                "courseCancelled": None,
                "instructors": [{"instructor": "CONRAD P T", "functionCode": "Teaching and in charge"}],
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
                "instructors": [{"instructor": "KHARITONOVA Y", "functionCode": "Teaching and in charge"}],
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

MOCK_QUARTER_RESPONSE = {
    "quarter": "20262",
    "qyy": "S26",
    "name": "SPRING 2026",
    "category": "SPRING",
    "academicYear": "2025-2026",
    "firstDayOfClasses": "2026-03-30",
    "lastDayOfClasses": "2026-06-05",
    "firstDayOfFinals": "2026-06-08",
    "lastDayOfFinals": "2026-06-12",
    "pass1Begin": "2026-02-23",
    "pass2Begin": "2026-03-02",
    "pass3Begin": "2026-03-09",
}


@pytest.fixture
def client():
    """Create a client with a test API key."""
    return UCSBApiClient(api_key="test-key-12345")


def test_client_requires_api_key():
    with patch("ucsb_api.client.settings") as mock_settings:
        mock_settings.ucsb_api_key = ""
        with pytest.raises(UCSBApiError, match="not configured"):
            UCSBApiClient(api_key="")


def test_client_sets_correct_headers(client):
    assert client._headers["ucsb-api-key"] == "test-key-12345"
    assert client._headers["accept"] == "application/json"


@patch("ucsb_api.client.requests.get")
def test_fetch_classes_success(mock_get, client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_CLASSES_RESPONSE
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    sections = client.fetch_classes("20262", "CMPSC 130A")

    assert len(sections) == 2
    assert sections[0]["enrollCode"] == "12345"
    assert sections[0]["_courseId"] == "CMPSC     130A"
    assert sections[0]["_quarter"] == "20262"

    # Verify correct API call
    call_kwargs = mock_get.call_args
    assert call_kwargs[1]["headers"]["ucsb-api-key"] == "test-key-12345"
    assert call_kwargs[1]["params"]["quarter"] == "20262"


@patch("ucsb_api.client.requests.get")
def test_fetch_classes_excludes_cancelled(mock_get, client):
    response_with_cancelled = [
        {
            "courseId": "CMPSC     130A",
            "title": "Data Structures",
            "classSections": [
                {"enrollCode": "111", "courseCancelled": True, "instructors": [], "timeLocations": []},
                {"enrollCode": "222", "courseCancelled": None, "instructors": [], "timeLocations": []},
            ],
        }
    ]
    mock_resp = MagicMock()
    mock_resp.json.return_value = response_with_cancelled
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    sections = client.fetch_classes("20262", "CMPSC 130A")
    assert len(sections) == 1
    assert sections[0]["enrollCode"] == "222"


@patch("ucsb_api.client.requests.get")
def test_fetch_classes_api_error(mock_get, client):
    import requests as req_lib

    mock_get.side_effect = req_lib.ConnectionError("Connection refused")

    with pytest.raises(UCSBApiError, match="Failed to fetch classes"):
        client.fetch_classes("20262", "CMPSC 130A")


@patch("ucsb_api.client.requests.get")
def test_fetch_quarter_calendar_success(mock_get, client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = MOCK_QUARTER_RESPONSE
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    result = client.fetch_quarter_calendar("20262")

    assert result["quarter"] == "20262"
    assert result["name"] == "SPRING 2026"
    assert result["firstDayOfClasses"] == "2026-03-30"
    assert result["pass1Begin"] == "2026-02-23"


@patch("ucsb_api.client.requests.get")
def test_fetch_current_quarter(mock_get, client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"quarter": "20262", "name": "SPRING 2026"}
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    result = client.fetch_current_quarter()
    assert result["quarter"] == "20262"


@patch("ucsb_api.client.requests.get")
def test_fetch_department_classes(mock_get, client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = MOCK_CLASSES_RESPONSE
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    sections = client.fetch_department_classes("20262", "CMPSC")
    assert len(sections) == 2


def _http_error_response(status_code):
    import requests as req_lib

    resp = MagicMock()
    resp.status_code = status_code
    resp.text = '{"title": "Bad Request"}'
    resp.raise_for_status.side_effect = req_lib.HTTPError(
        f"{status_code} Client Error", response=resp
    )
    return resp


@patch("ucsb_api.client.requests.get")
def test_fetch_department_classes_error_carries_status(mock_get, client):
    mock_get.return_value = _http_error_response(400)

    with pytest.raises(UCSBApiError) as excinfo:
        client.fetch_department_classes("20271", "ANTH")
    assert excinfo.value.status_code == 400


@patch("ucsb_api.client.requests.get")
def test_probe_department_classes_sends_one_nightly_shaped_request(mock_get, client):
    """The probe is page 1 of the exact request the nightly loop makes, nothing more."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = MOCK_CLASSES_RESPONSE * 100  # a full page
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    client.probe_department_classes("20271", "ANTH")

    mock_get.assert_called_once()
    params = mock_get.call_args[1]["params"]
    assert params == {
        "quarter": "20271",
        "subjectCode": "ANTH",
        "pageNumber": 1,
        "pageSize": 100,
        "includeClassSections": "true",
    }


@patch("ucsb_api.client.requests.get")
def test_probe_department_classes_raises_status_without_logging_error(mock_get, client, caplog):
    """A probe failure is the caller's call to report, so the client stays quiet."""
    mock_get.return_value = _http_error_response(400)

    with caplog.at_level("DEBUG", logger="ucsb_api.client"):
        with pytest.raises(UCSBApiError) as excinfo:
            client.probe_department_classes("20271", "ANTH")
    assert excinfo.value.status_code == 400
    assert not [r for r in caplog.records if r.levelname == "ERROR"]


@patch("ucsb_api.client.requests.get")
def test_probe_department_classes_connection_error_has_no_status(mock_get, client):
    import requests as req_lib

    mock_get.side_effect = req_lib.ConnectionError("Connection refused")

    with pytest.raises(UCSBApiError) as excinfo:
        client.probe_department_classes("20271", "ANTH")
    assert excinfo.value.status_code is None


# ---------------------------------------------------------------------------
# Quarter code utility tests
# ---------------------------------------------------------------------------

def test_get_next_quarter_code():
    assert get_next_quarter_code("20261") == "20262"  # Winter -> Spring
    assert get_next_quarter_code("20262") == "20263"  # Spring -> Summer
    assert get_next_quarter_code("20263") == "20264"  # Summer -> Fall
    assert get_next_quarter_code("20264") == "20271"  # Fall -> next year Winter


def test_quarter_code_to_name():
    assert quarter_code_to_name("20261") == "Winter 2026"
    assert quarter_code_to_name("20262") == "Spring 2026"
    assert quarter_code_to_name("20263") == "Summer 2026"
    assert quarter_code_to_name("20264") == "Fall 2026"


# ---------------------------------------------------------------------------
# Name matcher — parsing tests
# ---------------------------------------------------------------------------

def test_parse_standard_name():
    result = parse_ucsb_instructor("CONRAD P T")
    assert result is not None
    assert result.last_name == "conrad"
    assert result.initials == ["P", "T"]
    assert result.first_initial == "P"


def test_parse_single_initial():
    result = parse_ucsb_instructor("KHARITONOVA Y")
    assert result is not None
    assert result.last_name == "kharitonova"
    assert result.initials == ["Y"]
    assert result.first_initial == "Y"


def test_parse_no_initials():
    result = parse_ucsb_instructor("SMITH")
    assert result is not None
    assert result.last_name == "smith"
    assert result.initials == []
    assert result.first_initial is None


def test_parse_staff_returns_none():
    assert parse_ucsb_instructor("STAFF") is None
    assert parse_ucsb_instructor("T.B.A.") is None
    assert parse_ucsb_instructor("TBA") is None


def test_parse_empty_returns_none():
    assert parse_ucsb_instructor("") is None
    assert parse_ucsb_instructor("  ") is None


# ---------------------------------------------------------------------------
# Name matcher — professor name extraction
# ---------------------------------------------------------------------------

def test_extract_last_name_first_last():
    assert _extract_professor_last_name("Phill Conrad") == "conrad"


def test_extract_last_name_last_first():
    assert _extract_professor_last_name("Conrad, Phill") == "conrad"


def test_extract_last_name_with_suffix():
    assert _extract_professor_last_name("John Smith Jr.") == "smith"


def test_extract_first_initial_first_last():
    assert _extract_professor_first_initial("Phill Conrad") == "P"


def test_extract_first_initial_last_first():
    assert _extract_professor_first_initial("Conrad, Phill") == "P"


def test_extract_last_name_uppercase_last_first():
    """Nexus / UCSB-style names are uppercase, last name first, then initials."""
    assert _extract_professor_last_name("GURVEN M D") == "gurven"
    assert _extract_professor_last_name("HUANG L") == "huang"
    assert _extract_professor_last_name("CHANG SHIYU") == "chang"
    assert _extract_professor_last_name("VAN DER BERG J") == "van"


def test_extract_first_initial_uppercase_last_first():
    assert _extract_professor_first_initial("GURVEN M D") == "M"
    assert _extract_professor_first_initial("HUANG L") == "L"
    assert _extract_professor_first_initial("CHANG SHIYU") == "S"
    assert _extract_professor_first_initial("VAN DER BERG J") == "J"


# ---------------------------------------------------------------------------
# Name matcher — matching tests
# ---------------------------------------------------------------------------

PROFESSORS = [
    {"id": 1, "name_rmp": "Phill Conrad", "name_nexus": "CONRAD, PHILLIP"},
    {"id": 2, "name_rmp": "Yekaterina Kharitonova", "name_nexus": None},
    {"id": 3, "name_rmp": "Richert Wang", "name_nexus": "WANG, RICHERT"},
    {"id": 4, "name_rmp": "Diba Mirza", "name_nexus": "MIRZA, DIBAGHARAN"},
    {"id": 5, "name_rmp": "Kevin Conrad", "name_nexus": None},  # Same last name, different initial
]


def test_match_exact_with_initial():
    parsed = parse_ucsb_instructor("CONRAD P T")
    result = match_instructor_to_professor(parsed, PROFESSORS)
    assert result is not None
    assert result.professor_id == 1
    assert result.confidence == 1.0
    assert result.match_method == "exact"


def test_match_distinguishes_same_last_name():
    """CONRAD P T should match Phill Conrad (id=1), not Kevin Conrad (id=5)."""
    parsed = parse_ucsb_instructor("CONRAD P T")
    result = match_instructor_to_professor(parsed, PROFESSORS)
    assert result is not None
    assert result.professor_id == 1  # Phill, not Kevin


def test_match_single_initial():
    parsed = parse_ucsb_instructor("KHARITONOVA Y")
    result = match_instructor_to_professor(parsed, PROFESSORS)
    assert result is not None
    assert result.professor_id == 2


def test_match_wang():
    parsed = parse_ucsb_instructor("WANG R")
    result = match_instructor_to_professor(parsed, PROFESSORS)
    assert result is not None
    assert result.professor_id == 3


def test_match_no_professors():
    parsed = parse_ucsb_instructor("CONRAD P T")
    assert match_instructor_to_professor(parsed, []) is None


def test_match_unknown_instructor():
    parsed = parse_ucsb_instructor("ZZZZUNKNOWN X")
    result = match_instructor_to_professor(parsed, PROFESSORS)
    assert result is None


def test_match_staff_returns_none():
    parsed = parse_ucsb_instructor("STAFF")
    result = match_instructor_to_professor(parsed, PROFESSORS)
    assert result is None


def test_match_auto_created_ucsb_name():
    """A professor auto-created from a UCSB name must match that same name on later syncs."""
    professors = [{"id": 6, "name_rmp": None, "name_nexus": "GURVEN M D"}]
    parsed = parse_ucsb_instructor("GURVEN M D")
    result = match_instructor_to_professor(parsed, professors)
    assert result is not None
    assert result.professor_id == 6
    assert result.confidence == 1.0
    assert result.match_method == "exact"


def test_match_nexus_initial_only_name():
    """Nexus grade-data names like "HUANG L" match the UCSB form of the same name."""
    professors = [{"id": 7, "name_rmp": None, "name_nexus": "HUANG L"}]
    parsed = parse_ucsb_instructor("HUANG L")
    result = match_instructor_to_professor(parsed, professors)
    assert result is not None
    assert result.professor_id == 7


def test_match_uppercase_name_distinguishes_initial():
    """GURVEN M D must not match a stored GURVEN K."""
    professors = [{"id": 8, "name_rmp": None, "name_nexus": "GURVEN K"}]
    parsed = parse_ucsb_instructor("GURVEN M D")
    assert match_instructor_to_professor(parsed, professors) is None


# ---------------------------------------------------------------------------
# Name matcher — full given names and departments (2026-09-29: the nightly
# sync attached 352 Fall 2026 sections to the wrong professor)
# ---------------------------------------------------------------------------

def _prof(prof_id, name_nexus, department, name_rmp=None):
    return {"id": prof_id, "name_rmp": name_rmp, "name_nexus": name_nexus, "department": department}


def _match_id(raw, professors, department=None):
    result = match_instructor_to_professor(parse_ucsb_instructor(raw), professors, department)
    return result.professor_id if result else None


def test_match_prefers_the_exact_name_over_an_earlier_similar_one():
    """POPESCU P F's 129 sections went to POPESCU P E, the older row."""
    professors = [_prof(1, "POPESCU P E", "PHYS"), _prof(2, "POPESCU P F", "PHYS")]
    assert _match_id("POPESCU P F", professors, "PHYS") == 2


def test_match_rejects_a_different_second_initial():
    assert _match_id("POPESCU P F", [_prof(1, "POPESCU P E", "PHYS")], "PHYS") is None
    assert _match_id("WOODS M P", [_prof(1, "WOODS M J", "ED")], "ED") is None


def test_match_reads_full_given_names():
    """ZHAO XIAOLEI used to be read as last name ZHAO and no initials, so it
    matched the first ZHAO on file."""
    professors = [_prof(1, "ZHAO B Y", "MATH"), _prof(2, "ZHAO XIAOLEI", "MATH")]
    assert _match_id("ZHAO XIAOLEI", professors, "MATH") == 2
    assert _match_id("ZHAO XIAOLEI", professors[:1], "MATH") is None


def test_match_returns_none_when_two_people_fit():
    professors = [_prof(1, "WOODS M J", "ED"), _prof(2, "WOODS M P", "ED")]
    assert _match_id("WOODS M", professors, "ED") is None


def test_match_rows_sharing_a_name_count_as_one_person():
    professors = [_prof(1, "KOTH M K", "ART"), _prof(2, "KOTH M K", "ART")]
    assert _match_id("KOTH M", professors, "ART") == 1


def test_match_requires_the_section_department_unless_the_name_is_exact():
    """KIM TAEHWAN teaching MATH is not the KIM T of Media Arts."""
    professors = [_prof(1, "KIM T", "MAT")]
    assert _match_id("KIM TAEHWAN", professors, "MATH") is None
    assert _match_id("KIM TAEHWAN", professors, "MAT") == 1
    assert _match_id("KIM T", professors, "MATH") == 1  # same name: any department
    assert _match_id("KIM TAEHWAN", professors) == 1  # no department: as before


def test_match_treats_online_codes_as_their_department():
    assert _match_id("CHEN SIYU", [_prof(1, "CHEN S", "PSTAT")], "PSTATW") == 1
    assert _match_id("CHEN SIYU", [_prof(1, "CHEN S", "PSTATW")], "PSTAT") == 1


def test_match_reads_rmp_department_names():
    assert _match_id("MASOOD B", [_prof(1, None, "Statistics", "B. Masood")], "PSTAT") == 1
    assert _match_id("FU W", [_prof(1, None, "Philosophy", "Wade  Fu")], "MATH") is None


def test_match_prefers_a_nexus_row_over_an_unlinked_rmp_row():
    professors = [
        _prof(1, "HENDERSON O G", "ENGL"),
        _prof(2, None, "English", "Olivia Henderson"),
    ]
    assert _match_id("HENDERSON O", professors, "ENGL") == 1


def test_match_registrar_names_need_the_same_last_name():
    """The registrar spells a name one way; fuzzy last names are for RMP spellings."""
    assert _match_id("ZHANG S", [_prof(1, "HUANG SUNZEYU", "CHEM")], "CHEM") is None
    assert _match_id("CHEN A", [_prof(1, "COHEN A S", "PSY")], "PSY") is None
    rmp_only = [_prof(1, None, "Computer Science", "Yekaterina Kharitonova")]
    assert _match_id("KHARITONOV Y", rmp_only, "CMPSC") == 1


def test_match_full_given_name_needs_a_lone_initial():
    """As in pass 4: CHEN S may be CHEN SIYU, but WANG Y-D is not WANG YAXUAN."""
    assert _match_id("CHEN SIYU", [_prof(1, "CHEN S", "PSTAT")], "PSTAT") == 1
    assert _match_id("TROY K", [_prof(1, "TROY KRIS", "MCDB")], "MCDB") == 1
    assert _match_id("WANG YAXUAN", [_prof(1, "WANG Y-D", "PSTAT")], "PSTAT") is None
    assert _match_id("NGUYEN TRUC", [_prof(1, "NGUYEN T T", "CHEM")], "CHEM") is None
    # RMP names are first-name-first, so initials still match a full first name
    assert _match_id("CONRAD P T", [_prof(1, None, "Computer Science", "Phill Conrad")], "CMPSC") == 1

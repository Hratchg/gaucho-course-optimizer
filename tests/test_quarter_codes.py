"""ARCH-3: timezone-aware quarter-code derivation."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from ucsb_api.quarters import current_and_next_quarter_codes, current_quarter_code

PACIFIC = ZoneInfo("America/Los_Angeles")


def test_winter_through_march():
    assert current_quarter_code(date(2026, 1, 15)) == "20261"
    assert current_quarter_code(date(2026, 3, 31)) == "20261"


def test_spring_starts_april():
    assert current_quarter_code(date(2026, 4, 1)) == "20262"
    assert current_quarter_code(date(2026, 6, 30)) == "20262"


def test_summer_starts_july():
    assert current_quarter_code(date(2026, 7, 1)) == "20263"
    assert current_quarter_code(date(2026, 8, 31)) == "20263"


def test_fall_starts_september():
    assert current_quarter_code(date(2026, 9, 1)) == "20264"
    assert current_quarter_code(date(2026, 12, 31)) == "20264"


def test_december_to_january_rolls_the_year():
    assert current_and_next_quarter_codes(date(2026, 12, 15)) == ("20264", "20271")
    assert current_quarter_code(date(2027, 1, 1)) == "20271"


def test_naive_datetime_is_treated_as_pacific():
    assert current_quarter_code(datetime(2026, 9, 1, 0, 0, 0)) == "20264"


def test_utc_datetime_converts_to_pacific():
    # 2026-04-01 06:00 UTC is still March 31 in Los Angeles → Winter
    utc = datetime(2026, 4, 1, 6, 0, 0, tzinfo=ZoneInfo("UTC"))
    assert current_quarter_code(utc) == "20261"
    # 2026-04-01 08:00 UTC is April 1 01:00 PDT → Spring
    later = datetime(2026, 4, 1, 8, 0, 0, tzinfo=ZoneInfo("UTC"))
    assert current_quarter_code(later) == "20262"

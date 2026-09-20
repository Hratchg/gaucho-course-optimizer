"""Timezone-aware UCSB quarter-code helpers.

Quarter codes are YYYYQ where Q: 1=Winter, 2=Spring, 3=Summer, 4=Fall.
Calendar cutovers match the historical month branches (Jan–Mar Winter,
Apr–Jun Spring, Jul–Aug Summer, Sep–Dec Fall) but are evaluated in
America/Los_Angeles so UTC servers do not flip a day early.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from ucsb_api.client import get_next_quarter_code

PACIFIC = ZoneInfo("America/Los_Angeles")


def current_quarter_code(when: date | datetime | None = None) -> str:
    """Return the YYYYQ code for `when` (defaults to now, Pacific time)."""
    local_date = _as_pacific_date(when)
    year = local_date.year
    month = local_date.month
    if month <= 3:
        quarter = 1
    elif month <= 6:
        quarter = 2
    elif month <= 8:
        quarter = 3
    else:
        quarter = 4
    return f"{year}{quarter}"


def current_and_next_quarter_codes(
    when: date | datetime | None = None,
) -> tuple[str, str]:
    """Return (current, next) quarter codes for `when`."""
    current = current_quarter_code(when)
    return current, get_next_quarter_code(current)


def _as_pacific_date(when: date | datetime | None) -> date:
    if when is None:
        return datetime.now(PACIFIC).date()
    if isinstance(when, datetime):
        if when.tzinfo is None:
            when = when.replace(tzinfo=PACIFIC)
        return when.astimezone(PACIFIC).date()
    return when

"""Quarter info endpoint for registration countdown.

Provides current quarter name, next quarter code, and pass dates
from the UCSB Quarter Calendar API, with a date-derived fallback so a
UCSB outage (BUG-13) cannot 502 the whole banner.
"""

import logging

from fastapi import APIRouter
from pydantic import BaseModel

from ucsb_api.client import UCSBApiClient, UCSBApiError, get_next_quarter_code, quarter_code_to_name
from ucsb_api.quarters import current_quarter_code

logger = logging.getLogger(__name__)

router = APIRouter()

# Last successful UCSB calendar payload. Quarter boundaries change four
# times a year, so a stale cache is still useful for pass dates during
# a multi-hour upstream outage.
_LAST_GOOD: "QuarterInfoResponse | None" = None


class QuarterInfoResponse(BaseModel):
    """Response for GET /quarters/current."""

    quarter_code: str
    quarter_name: str
    next_quarter_code: str
    next_quarter_name: str
    pass1_begin: str | None = None
    pass2_begin: str | None = None
    pass3_begin: str | None = None
    first_day_of_classes: str | None = None
    last_day_of_classes: str | None = None


def _fallback_quarter_info() -> QuarterInfoResponse:
    current = current_quarter_code()
    nxt = get_next_quarter_code(current)
    return QuarterInfoResponse(
        quarter_code=current,
        quarter_name=quarter_code_to_name(current),
        next_quarter_code=nxt,
        next_quarter_name=quarter_code_to_name(nxt),
    )


def reset_quarter_cache() -> None:
    """Test helper — drop the last-good cache."""
    global _LAST_GOOD
    _LAST_GOOD = None


@router.get("/current", response_model=QuarterInfoResponse)
def get_current_quarter():
    """Return current quarter info with pass dates for registration countdown.

    Fetches from the UCSB Quarter Calendar API. The pass dates are for the
    next quarter (the one students will register for). On upstream failure
    returns the last good response, or a date-derived quarter with null
    pass dates — never 502 (BUG-13).
    """
    global _LAST_GOOD

    try:
        client = UCSBApiClient()
    except UCSBApiError:
        logger.error("UCSB API key not configured; serving cached or date-derived quarter")
        return _LAST_GOOD or _fallback_quarter_info()

    try:
        current = client.fetch_current_quarter()
        current_code = current.get("quarter", "")
        current_name = current.get("name", "")

        next_code = get_next_quarter_code(current_code)
        next_calendar = client.fetch_quarter_calendar(next_code)
        next_name = next_calendar.get("name", "") or quarter_code_to_name(next_code)

        result = QuarterInfoResponse(
            quarter_code=current_code,
            quarter_name=current_name,
            next_quarter_code=next_code,
            next_quarter_name=next_name,
            pass1_begin=next_calendar.get("pass1Begin"),
            pass2_begin=next_calendar.get("pass2Begin"),
            pass3_begin=next_calendar.get("pass3Begin"),
            first_day_of_classes=next_calendar.get("firstDayOfClasses"),
            last_day_of_classes=next_calendar.get("lastDayOfClasses"),
        )
        _LAST_GOOD = result
        return result
    except UCSBApiError as exc:
        logger.error("Failed to fetch quarter info: %s", exc)
        if _LAST_GOOD is not None:
            return _LAST_GOOD
        return _fallback_quarter_info()

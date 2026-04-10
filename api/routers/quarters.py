"""Quarter info endpoint for registration countdown.

Provides current quarter name, next quarter code, and pass dates
from the UCSB Quarter Calendar API.
"""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ucsb_api.client import UCSBApiClient, UCSBApiError, get_next_quarter_code

logger = logging.getLogger(__name__)

router = APIRouter()


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


@router.get("/current", response_model=QuarterInfoResponse)
def get_current_quarter():
    """Return current quarter info with pass dates for registration countdown.

    Fetches from the UCSB Quarter Calendar API. The pass dates are for the
    next quarter (the one students will register for).
    """
    try:
        client = UCSBApiClient()
    except UCSBApiError:
        raise HTTPException(
            status_code=503,
            detail="UCSB API key not configured",
        )

    try:
        current = client.fetch_current_quarter()
        current_code = current.get("quarter", "")
        current_name = current.get("name", "")

        # Get next quarter info (the one students register for)
        next_code = get_next_quarter_code(current_code)
        next_calendar = client.fetch_quarter_calendar(next_code)

        from ucsb_api.client import quarter_code_to_name

        next_name = next_calendar.get("name", "") or quarter_code_to_name(next_code)

        return QuarterInfoResponse(
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
    except UCSBApiError as exc:
        logger.error("Failed to fetch quarter info: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="Failed to fetch quarter info from UCSB API",
        )

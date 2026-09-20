"""UCSB API client for Academic Curriculums and Quarter Calendar endpoints.

Docs:
  - Classes: https://developer.ucsb.edu/content/academic-curriculums
  - Calendar: https://developer.ucsb.edu/content/academic-quarter-calendar

Auth: header ``ucsb-api-key`` with value from ``UCSB_API_KEY`` env var.
Quarter code format: YYYYQ where Q: 1=Winter, 2=Spring, 3=Summer, 4=Fall.
"""

import logging
from typing import Any

import requests

from api.config import settings

logger = logging.getLogger(__name__)

CLASSES_BASE_URL = "https://api.ucsb.edu/academics/curriculums/v3/classes"
QUARTER_CALENDAR_URL = "https://api.ucsb.edu/academics/quartercalendar/v1/quarters"

# Timeout in seconds for UCSB API requests
REQUEST_TIMEOUT = 15


class UCSBApiError(Exception):
    """Raised when a UCSB API request fails."""


class UCSBApiClient:
    """Client for UCSB public data APIs."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.ucsb_api_key
        if not self.api_key:
            raise UCSBApiError("UCSB_API_KEY is not configured")
        self._headers = {"ucsb-api-key": self.api_key, "accept": "application/json"}

    # ------------------------------------------------------------------
    # Academic Curriculums — class sections
    # ------------------------------------------------------------------

    def fetch_classes(
        self,
        quarter_code: str,
        course_id: str,
        *,
        include_cancelled: bool = False,
    ) -> list[dict[str, Any]]:
        """Fetch class sections for a quarter + course from the UCSB API.

        Parameters
        ----------
        quarter_code : str
            YYYYQ format, e.g. "20262" for Spring 2026.
        course_id : str
            Department + number, e.g. "CMPSC 130A" (whitespace is OK;
            the API expects the padded 13-char format internally, but the
            search endpoint handles flexible input).

        Returns
        -------
        list[dict]
            Raw section dicts from the API (classSections array items).
        """
        params = {
            "quarter": quarter_code,
            "courseId": course_id.strip(),
            "pageNumber": 1,
            "pageSize": 100,
            "includeClassSections": "true",
        }

        all_sections: list[dict[str, Any]] = []
        page = 1

        while True:
            params["pageNumber"] = page
            try:
                resp = requests.get(
                    CLASSES_BASE_URL + "/search",
                    headers=self._headers,
                    params=params,
                    timeout=REQUEST_TIMEOUT,
                )
                resp.raise_for_status()
            except requests.RequestException as exc:
                logger.error("UCSB classes API error (page %d): %s", page, exc)
                raise UCSBApiError(f"Failed to fetch classes: {exc}") from exc

            data = resp.json()
            classes = data if isinstance(data, list) else data.get("classes", [])

            for cls in classes:
                sections = cls.get("classSections", [])
                for sec in sections:
                    # Attach course-level metadata to each section for convenience
                    sec["_courseId"] = cls.get("courseId", "").strip()
                    sec["_title"] = cls.get("title", "")
                    sec["_quarter"] = quarter_code
                    if not include_cancelled and sec.get("courseCancelled"):
                        continue
                    all_sections.append(sec)

            # If fewer results than page size, we have all pages
            if len(classes) < params["pageSize"]:
                break
            page += 1

        logger.info(
            "Fetched %d sections for %s in quarter %s",
            len(all_sections),
            course_id,
            quarter_code,
        )
        return all_sections

    def fetch_department_classes(
        self,
        quarter_code: str,
        department: str,
    ) -> list[dict[str, Any]]:
        """Fetch all class sections for a department in a quarter.

        Used by the nightly bulk refresh job.
        """
        params = {
            "quarter": quarter_code,
            "subjectCode": department.strip(),
            "pageNumber": 1,
            "pageSize": 100,
            "includeClassSections": "true",
        }

        all_sections: list[dict[str, Any]] = []
        page = 1

        while True:
            params["pageNumber"] = page
            try:
                resp = requests.get(
                    CLASSES_BASE_URL + "/search",
                    headers=self._headers,
                    params=params,
                    timeout=REQUEST_TIMEOUT,
                )
                resp.raise_for_status()
            except requests.RequestException as exc:
                logger.error("UCSB dept classes API error (page %d): %s", page, exc)
                raise UCSBApiError(f"Failed to fetch dept classes: {exc}") from exc

            data = resp.json()
            classes = data if isinstance(data, list) else data.get("classes", [])

            for cls in classes:
                sections = cls.get("classSections", [])
                for sec in sections:
                    sec["_courseId"] = cls.get("courseId", "").strip()
                    sec["_title"] = cls.get("title", "")
                    sec["_quarter"] = quarter_code
                    if sec.get("courseCancelled"):
                        continue
                    all_sections.append(sec)

            if len(classes) < params["pageSize"]:
                break
            page += 1

        logger.info(
            "Fetched %d sections for department %s in quarter %s",
            len(all_sections),
            department,
            quarter_code,
        )
        return all_sections

    # ------------------------------------------------------------------
    # Quarter Calendar
    # ------------------------------------------------------------------

    def fetch_quarter_calendar(self, quarter_code: str) -> dict[str, Any]:
        """Fetch quarter calendar info (dates, pass times, finals).

        Parameters
        ----------
        quarter_code : str
            YYYYQ format, e.g. "20262".

        Returns
        -------
        dict
            Parsed quarter info with keys: quarter, name, firstDayOfClasses,
            lastDayOfClasses, firstDayOfFinals, lastDayOfFinals, pass1Begin,
            pass2Begin, pass3Begin.
        """
        url = f"{QUARTER_CALENDAR_URL}/{quarter_code}"
        try:
            resp = requests.get(
                url,
                headers=self._headers,
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            logger.error("UCSB quarter calendar API error (status=%s): %s", status, exc)
            raise UCSBApiError(
                f"Failed to fetch quarter calendar (status={status}): {exc}"
            ) from exc

        data = resp.json()
        logger.info("Fetched quarter calendar for %s: %s", quarter_code, data.get("name", ""))
        return data

    def fetch_current_quarter(self) -> dict[str, Any]:
        """Fetch the current quarter info.

        Hits /quarters/current to determine what quarter we are in.
        """
        url = f"{QUARTER_CALENDAR_URL}/current"
        try:
            resp = requests.get(
                url,
                headers=self._headers,
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            logger.error("UCSB current quarter API error (status=%s): %s", status, exc)
            raise UCSBApiError(
                f"Failed to fetch current quarter (status={status}): {exc}"
            ) from exc

        return resp.json()


def get_next_quarter_code(current_quarter_code: str) -> str:
    """Derive the next quarter code from the current one.

    Quarter codes: YYYYQ where Q: 1=Winter, 2=Spring, 3=Summer, 4=Fall.
    After Fall (4), next is Winter (1) of the following year.
    """
    year = int(current_quarter_code[:4])
    q = int(current_quarter_code[4])
    if q == 4:
        return f"{year + 1}1"
    return f"{year}{q + 1}"


def quarter_code_to_name(quarter_code: str) -> str:
    """Convert a quarter code like '20262' to a human-readable name like 'Spring 2026'."""
    names = {1: "Winter", 2: "Spring", 3: "Summer", 4: "Fall"}
    year = quarter_code[:4]
    q = int(quarter_code[4])
    return f"{names.get(q, 'Unknown')} {year}"

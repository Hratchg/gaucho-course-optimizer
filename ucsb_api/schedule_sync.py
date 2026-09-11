"""Schedule sync pipeline: fetch UCSB sections, match instructors, store in DB.

This module orchestrates:
  1. Fetching class sections from the UCSB API
  2. Parsing instructor names
  3. Matching instructors to existing professor records
  4. Upserting ScheduledSection rows in the database
"""

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import and_
from sqlalchemy.orm import Session

from db.models import Course, Professor, ScheduledSection
from ucsb_api.client import UCSBApiClient, quarter_code_to_name
from ucsb_api.name_matcher import (
    match_instructor_to_professor,
    parse_ucsb_instructor,
)

logger = logging.getLogger(__name__)


def _normalize_course_id(raw_course_id: str) -> str:
    """Normalize a padded UCSB course ID like ``"CMPSC     130A"`` to ``"CMPSC130A"``.

    Removes all whitespace to match the DB format (e.g., "CMPSC130A").
    """
    return raw_course_id.replace(" ", "")


def _extract_section_data(section: dict[str, Any]) -> dict[str, Any]:
    """Extract relevant fields from a raw UCSB API section dict."""
    # Get primary instructor
    instructors = section.get("instructors", [])
    primary_instructor = None
    for inst in instructors:
        if inst.get("functionCode", "").startswith("Teaching"):
            primary_instructor = inst.get("instructor", "")
            break
    if not primary_instructor and instructors:
        primary_instructor = instructors[0].get("instructor", "")

    # Get primary time/location
    time_locs = section.get("timeLocations", [])
    days = begin_time = end_time = building = room = None
    if time_locs:
        tl = time_locs[0]
        days = tl.get("days")
        begin_time = tl.get("beginTime")
        end_time = tl.get("endTime")
        building = tl.get("building")
        room = tl.get("room")

    return {
        "enroll_code": str(section.get("enrollCode", "")),
        "instructor_name_raw": primary_instructor,
        "days": days,
        "begin_time": begin_time,
        "end_time": end_time,
        "building": building,
        "room": room,
        "enrolled": section.get("enrolledTotal"),
        "max_enroll": section.get("maxEnroll"),
        "section_cancelled": bool(section.get("courseCancelled")),
    }


def _build_professor_lookup(session: Session) -> list[dict]:
    """Load all professors into a list of dicts for the name matcher.

    Oldest first, so an exact match lands on the canonical row rather than a
    later duplicate.
    """
    profs = session.query(Professor).order_by(Professor.id).all()
    return [
        {"id": p.id, "name_rmp": p.name_rmp, "name_nexus": p.name_nexus}
        for p in profs
    ]


def _auto_create_professor(
    session: Session,
    raw_name: str,
    department: str,
    cache: dict[str, int],
) -> int:
    """Create a minimal professor record for an unmatched UCSB instructor.

    Uses a per-run cache (keyed by raw_name) to avoid creating duplicates
    within the same sync session.

    Returns the professor ID.
    """
    cache_key = raw_name.strip().upper()
    if cache_key in cache:
        return cache[cache_key]

    prof = Professor(
        name_nexus=raw_name.strip(),
        department=department,
    )
    session.add(prof)
    session.flush()  # assign ID without committing
    cache[cache_key] = prof.id
    logger.info("Auto-created professor record for %s (id=%d, dept=%s)", raw_name, prof.id, department)
    return prof.id


def _find_course_by_code(session: Session, normalized_code: str) -> Course | None:
    """Look up a course by its normalized code."""
    return session.query(Course).filter(Course.code == normalized_code).first()


def sync_course_sections(
    session: Session,
    quarter_code: str,
    course_code: str,
    *,
    client: UCSBApiClient | None = None,
) -> dict[str, int]:
    """Fetch and store sections for a single course in a quarter.

    Parameters
    ----------
    session : Session
        SQLAlchemy database session.
    quarter_code : str
        YYYYQ format, e.g. "20262".
    course_code : str
        Course code as stored in DB, e.g. "CMPSC 130A".
    client : UCSBApiClient, optional
        Injected client (for testing). Created from settings if not provided.

    Returns
    -------
    dict with keys: inserted, updated, matched, unmatched
    """
    if client is None:
        client = UCSBApiClient()

    quarter_name = quarter_code_to_name(quarter_code)
    stats = {"inserted": 0, "updated": 0, "matched": 0, "unmatched": 0}

    # Look up the course in our DB
    course = _find_course_by_code(session, course_code)
    if not course:
        logger.warning("Course %s not found in database, skipping", course_code)
        return stats

    # Fetch sections from UCSB API
    try:
        raw_sections = client.fetch_classes(quarter_code, course_code)
    except Exception as exc:
        logger.error("Failed to fetch sections for %s: %s", course_code, exc)
        return stats

    if not raw_sections:
        logger.info("No sections found for %s in %s", course_code, quarter_code)
        return stats

    # Load professors for name matching
    professors = _build_professor_lookup(session)
    now = datetime.now(timezone.utc)

    for raw_section in raw_sections:
        section_data = _extract_section_data(raw_section)

        # Match instructor to professor
        professor_id = None
        if section_data["instructor_name_raw"]:
            parsed = parse_ucsb_instructor(section_data["instructor_name_raw"])
            if parsed:
                match = match_instructor_to_professor(parsed, professors)
                if match:
                    professor_id = match.professor_id
                    stats["matched"] += 1
                else:
                    stats["unmatched"] += 1

        # Upsert: check if section already exists by quarter_code + enroll_code
        existing = (
            session.query(ScheduledSection)
            .filter(
                and_(
                    ScheduledSection.quarter_code == quarter_code,
                    ScheduledSection.enroll_code == section_data["enroll_code"],
                )
            )
            .first()
        )

        if existing:
            # Update mutable fields
            existing.professor_id = professor_id
            existing.course_id = course.id
            existing.instructor_name_raw = section_data["instructor_name_raw"]
            existing.days = section_data["days"]
            existing.begin_time = section_data["begin_time"]
            existing.end_time = section_data["end_time"]
            existing.building = section_data["building"]
            existing.room = section_data["room"]
            existing.enrolled = section_data["enrolled"]
            existing.max_enroll = section_data["max_enroll"]
            existing.section_cancelled = section_data["section_cancelled"]
            existing.fetched_at = now
            stats["updated"] += 1
        else:
            new_section = ScheduledSection(
                professor_id=professor_id,
                course_id=course.id,
                quarter_code=quarter_code,
                quarter_name=quarter_name,
                enroll_code=section_data["enroll_code"],
                instructor_name_raw=section_data["instructor_name_raw"],
                days=section_data["days"],
                begin_time=section_data["begin_time"],
                end_time=section_data["end_time"],
                building=section_data["building"],
                room=section_data["room"],
                enrolled=section_data["enrolled"],
                max_enroll=section_data["max_enroll"],
                section_cancelled=section_data["section_cancelled"],
                fetched_at=now,
            )
            session.add(new_section)
            stats["inserted"] += 1

    session.commit()
    logger.info(
        "Synced %s in %s: %d inserted, %d updated, %d matched, %d unmatched",
        course_code,
        quarter_code,
        stats["inserted"],
        stats["updated"],
        stats["matched"],
        stats["unmatched"],
    )
    return stats


def sync_department_sections(
    session: Session,
    quarter_code: str,
    department: str,
    *,
    client: UCSBApiClient | None = None,
    auto_create_cache: dict[str, int] | None = None,
) -> dict[str, int]:
    """Fetch and store sections for all courses in a department.

    Used by the nightly bulk refresh job.

    Parameters
    ----------
    auto_create_cache : dict, optional
        Shared cache for auto-created professor records across departments.
        If None, a local cache is created for this call.
    """
    if client is None:
        client = UCSBApiClient()
    if auto_create_cache is None:
        auto_create_cache = {}

    quarter_name = quarter_code_to_name(quarter_code)
    total_stats = {"inserted": 0, "updated": 0, "matched": 0, "unmatched": 0, "auto_created": 0}

    try:
        raw_sections = client.fetch_department_classes(quarter_code, department)
    except Exception as exc:
        logger.error("Failed to fetch department %s: %s", department, exc)
        return total_stats

    if not raw_sections:
        logger.info("No sections for department %s in %s", department, quarter_code)
        return total_stats

    # Load professors for name matching
    professors = _build_professor_lookup(session)
    now = datetime.now(timezone.utc)

    # Group sections by course
    for raw_section in raw_sections:
        section_data = _extract_section_data(raw_section)
        raw_course_id = raw_section.get("_courseId", "")
        normalized_code = _normalize_course_id(raw_course_id)

        # Look up course
        course = _find_course_by_code(session, normalized_code)
        if not course:
            # Course not in our DB — skip (we only track courses with grade data)
            continue

        # Match instructor
        professor_id = None
        if section_data["instructor_name_raw"]:
            parsed = parse_ucsb_instructor(section_data["instructor_name_raw"])
            if parsed:
                match = match_instructor_to_professor(parsed, professors)
                if match:
                    professor_id = match.professor_id
                    total_stats["matched"] += 1
                else:
                    # Auto-create a professor record so future data can attach
                    professor_id = _auto_create_professor(
                        session,
                        section_data["instructor_name_raw"],
                        department,
                        auto_create_cache,
                    )
                    total_stats["auto_created"] += 1

        # Upsert
        existing = (
            session.query(ScheduledSection)
            .filter(
                and_(
                    ScheduledSection.quarter_code == quarter_code,
                    ScheduledSection.enroll_code == section_data["enroll_code"],
                )
            )
            .first()
        )

        if existing:
            existing.professor_id = professor_id
            existing.course_id = course.id
            existing.instructor_name_raw = section_data["instructor_name_raw"]
            existing.days = section_data["days"]
            existing.begin_time = section_data["begin_time"]
            existing.end_time = section_data["end_time"]
            existing.building = section_data["building"]
            existing.room = section_data["room"]
            existing.enrolled = section_data["enrolled"]
            existing.max_enroll = section_data["max_enroll"]
            existing.section_cancelled = section_data["section_cancelled"]
            existing.fetched_at = now
            total_stats["updated"] += 1
        else:
            new_section = ScheduledSection(
                professor_id=professor_id,
                course_id=course.id,
                quarter_code=quarter_code,
                quarter_name=quarter_name,
                enroll_code=section_data["enroll_code"],
                instructor_name_raw=section_data["instructor_name_raw"],
                days=section_data["days"],
                begin_time=section_data["begin_time"],
                end_time=section_data["end_time"],
                building=section_data["building"],
                room=section_data["room"],
                enrolled=section_data["enrolled"],
                max_enroll=section_data["max_enroll"],
                section_cancelled=section_data["section_cancelled"],
                fetched_at=now,
            )
            session.add(new_section)
            total_stats["inserted"] += 1

    session.commit()
    logger.info(
        "Synced department %s in %s: %d inserted, %d updated, %d matched, %d auto-created",
        department,
        quarter_code,
        total_stats["inserted"],
        total_stats["updated"],
        total_stats["matched"],
        total_stats["auto_created"],
    )
    return total_stats

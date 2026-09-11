"""Match UCSB API instructor names to existing professor records.

UCSB API returns instructor names in the format ``"LASTNAME F M"``
(uppercase, last name first, followed by first/middle initials).

This module parses that format and fuzzy-matches against the ``professors``
table using:
  1. Exact last-name match (case-insensitive) + first-initial match
  2. Fuzzy last-name match via Levenshtein distance (thefuzz) + first-initial
  3. Fuzzy last-name-only match as a fallback
"""

import logging
import re
from dataclasses import dataclass

from thefuzz import fuzz

logger = logging.getLogger(__name__)

# Minimum fuzzy match score (0-100) to consider a match
FUZZY_THRESHOLD = 80


@dataclass
class ParsedInstructor:
    """Parsed UCSB instructor name."""

    raw: str
    last_name: str  # lowercase
    initials: list[str]  # uppercase single characters

    @property
    def first_initial(self) -> str | None:
        return self.initials[0] if self.initials else None


def parse_ucsb_instructor(raw_name: str) -> ParsedInstructor | None:
    """Parse a UCSB instructor name like ``"CONRAD P T"`` into components.

    Returns None if the name is empty, "STAFF", or unparseable.
    """
    if not raw_name or not raw_name.strip():
        return None

    cleaned = raw_name.strip()
    if cleaned.upper() in ("STAFF", "T.B.A.", "TBA", "T B A"):
        return None

    parts = cleaned.split()
    if not parts:
        return None

    last_name = parts[0].lower()
    # Remaining parts are initials (single letters) — filter out non-alpha
    initials = [p.upper() for p in parts[1:] if len(p) == 1 and p.isalpha()]

    return ParsedInstructor(raw=raw_name, last_name=last_name, initials=initials)


def _split_uppercase_last_first(name: str) -> tuple[str, str | None]:
    """Split an uppercase last-name-first name into (last name, first initial).

    Both the Daily Nexus grade data ("HUANG L", "CHANG SHIYU") and the UCSB API
    ("GURVEN M D" — also what auto-created professors store) write names this
    way, whereas RMP names are mixed case ("Phill Conrad").
    """
    parts = name.split()
    last = parts[0].lower()
    rest = parts[1:]
    # Prefer a standalone initial so "VAN DER BERG J" pairs with the UCSB parse
    initials = [p for p in rest if len(p) == 1 and p.isalpha()]
    if initials:
        return last, initials[0].upper()
    if rest:
        first_alpha = next((c for c in rest[0] if c.isalpha()), None)
        return last, first_alpha.upper() if first_alpha else None
    return last, None


def _extract_professor_last_name(professor_name: str) -> str:
    """Extract last name from a professor's stored name.

    Handles formats like:
      - "Phill Conrad" -> "conrad"
      - "Conrad, Phill" -> "conrad"
      - "GURVEN M D" / "CHANG SHIYU" -> "gurven" / "chang" (uppercase = last first)
      - "John Smith Jr." -> "smith" (best effort)
    """
    if not professor_name:
        return ""

    name = professor_name.strip()

    # Handle "Last, First" format
    if "," in name:
        return name.split(",")[0].strip().lower()

    # Uppercase names come from Nexus / the UCSB API and are last-name-first
    if name.isupper():
        return _split_uppercase_last_first(name)[0]

    # Handle "First Last" format — take the last word
    parts = name.split()
    if len(parts) >= 2:
        # Skip suffixes like "Jr.", "III", "PhD"
        suffixes = {"jr", "jr.", "sr", "sr.", "ii", "iii", "iv", "phd", "ph.d."}
        last = parts[-1].lower()
        if last in suffixes and len(parts) >= 3:
            return parts[-2].lower()
        return last

    return parts[0].lower() if parts else ""


def _extract_professor_first_initial(professor_name: str) -> str | None:
    """Extract first initial from a professor's stored name."""
    if not professor_name:
        return None

    name = professor_name.strip()

    # Handle "Last, First" format
    if "," in name:
        parts = name.split(",")
        if len(parts) >= 2:
            first = parts[1].strip()
            return first[0].upper() if first else None
        return None

    # Uppercase names come from Nexus / the UCSB API and are last-name-first
    if name.isupper():
        return _split_uppercase_last_first(name)[1]

    # Handle "First Last" format
    parts = name.split()
    if parts:
        return parts[0][0].upper()

    return None


@dataclass
class MatchResult:
    """Result of matching an instructor to a professor."""

    professor_id: int
    professor_name: str
    confidence: float  # 0.0 to 1.0
    match_method: str  # "exact", "fuzzy", "last_name_only"


def match_instructor_to_professor(
    parsed: ParsedInstructor,
    professors: list[dict],
) -> MatchResult | None:
    """Match a parsed UCSB instructor name to an existing professor record.

    Parameters
    ----------
    parsed : ParsedInstructor
        The parsed instructor name from the UCSB API.
    professors : list[dict]
        Each dict must have keys: ``id``, ``name_rmp``, ``name_nexus``.

    Returns
    -------
    MatchResult or None
        The best match, or None if no match meets the threshold.
    """
    if not parsed or not professors:
        return None

    best_match: MatchResult | None = None
    best_score = 0.0

    for prof in professors:
        prof_id = prof["id"]
        # Try both name sources
        for name_field in ("name_rmp", "name_nexus"):
            prof_name = prof.get(name_field)
            if not prof_name:
                continue

            prof_last = _extract_professor_last_name(prof_name)
            prof_first_initial = _extract_professor_first_initial(prof_name)

            if not prof_last:
                continue

            # --- Strategy 1: Exact last name + first initial ---
            if prof_last == parsed.last_name:
                if parsed.first_initial and prof_first_initial:
                    if parsed.first_initial == prof_first_initial:
                        # Perfect match
                        return MatchResult(
                            professor_id=prof_id,
                            professor_name=prof_name,
                            confidence=1.0,
                            match_method="exact",
                        )
                    else:
                        # Same last name but different initial — could be a
                        # different person, so skip
                        continue
                else:
                    # Exact last name but no initials to compare — decent match
                    score = 0.85
                    if score > best_score:
                        best_score = score
                        best_match = MatchResult(
                            professor_id=prof_id,
                            professor_name=prof_name,
                            confidence=score,
                            match_method="exact",
                        )

            # --- Strategy 2: Fuzzy last name + first initial ---
            fuzzy_score = fuzz.ratio(prof_last, parsed.last_name)
            if fuzzy_score >= FUZZY_THRESHOLD:
                normalized = fuzzy_score / 100.0

                # Bonus if first initial matches
                if (
                    parsed.first_initial
                    and prof_first_initial
                    and parsed.first_initial == prof_first_initial
                ):
                    score = min(normalized + 0.1, 0.99)
                    method = "fuzzy"
                elif parsed.first_initial and prof_first_initial:
                    # Different initials — penalize
                    continue
                else:
                    score = normalized * 0.8
                    method = "last_name_only"

                if score > best_score:
                    best_score = score
                    best_match = MatchResult(
                        professor_id=prof_id,
                        professor_name=prof_name,
                        confidence=round(score, 2),
                        match_method=method,
                    )

    if best_match and best_match.confidence >= 0.6:
        return best_match

    if parsed:
        logger.warning("No match found for instructor: %s", parsed.raw)
    return None

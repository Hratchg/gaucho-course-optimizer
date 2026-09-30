"""Match UCSB API instructor names to existing professor records.

UCSB API returns instructor names in the format ``"LASTNAME F M"``
(uppercase, last name first, followed by first/middle initials), or with a
full given name for some instructors (``"ZHAO XIAOLEI"``).

This module parses that format and matches it against the ``professors``
table using:
  1. The exact name: a ``name_nexus`` equal to the UCSB name (oldest row wins)
  2. Exact last name + every given name or initial agreeing
  3. Fuzzy last name via Levenshtein distance (thefuzz) + given names agreeing,
     for RMP names only: the registrar spells a name the same way in the
     grades and the schedule, so "ZHANG S" is not "HUANG SUNZEYU"
  4. Last name alone, when one side has no given names
Matches 2-4 must also be in the section's department when it is known: a
"KIM TAEHWAN" teaching MATH is not the "KIM T" who teaches MAT. When several
different people still fit equally well nobody is picked, and the sync
creates a professor under the UCSB name instead of guessing.
"""

import logging
import re
from dataclasses import dataclass, field

from thefuzz import fuzz

from etl.department_mapper import departments_match

logger = logging.getLogger(__name__)

# Minimum fuzzy match score (0-100) to consider a match
FUZZY_THRESHOLD = 80


@dataclass
class ParsedInstructor:
    """Parsed UCSB instructor name."""

    raw: str
    last_name: str  # lowercase
    initials: list[str]  # uppercase single characters
    # Every given name or initial after the last name, uppercase ("XIAOLEI").
    given: list[str] = field(default_factory=list)

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

    return ParsedInstructor(
        raw=raw_name, last_name=last_name, initials=initials,
        given=_given_tokens(" ".join(parts[1:])),
    )


def _normalize_name(name: str | None) -> str:
    return " ".join((name or "").split()).upper()


def _in_department(section_dept: str, prof_dept: str | None) -> bool:
    """True when a professor's stored department is the section's department.

    Online sections have their own codes ("PSTATW" for PSTAT), and professors
    created from RMP alone store RMP's department name ("Mathematics").
    """
    code = _normalize_name(section_dept)
    stored = " ".join((prof_dept or "").split())
    if not code or not stored:
        return False
    if not stored.isupper():
        return any(departments_match(c, stored) for c in {code, code.removesuffix("W")} if c)
    stored = stored.upper()
    return code == stored or code == stored + "W" or stored == code + "W"


def _given_tokens(text: str) -> list[str]:
    """Uppercase given names and initials; hyphens and dots split them ("Y-D" -> Y, D)."""
    return [t for t in re.split(r"[^A-Za-z']+", text.upper()) if t]


def _given_names_agree(left: list[str], right: list[str], registrar: bool = False) -> bool:
    """True when two lists of given names could belong to the same person.

    Position by position, the first letters must match, and two full names
    must be the same name or one a truncation of the other (Nexus cuts names
    at 13 characters). An initial agrees with any name starting with it, and
    the longer list's extra names are ignored, so "SMITH J" agrees with
    "SMITH J R" but "POPESCU P F" does not agree with "POPESCU P E".

    Between two registrar names (``registrar``), a full given name agrees
    only with a lone initial, the pairs pass 4 merges
    (etl.name_utils.find_duplicate_pairs): "CHEN S" may be CHEN SIYU, but
    WANG Y-D, with two initials, is not WANG YAXUAN.
    """
    for a, b in zip(left, right):
        if a[0] != b[0]:
            return False
        if len(a) > 1 and len(b) > 1 and not (a.startswith(b) or b.startswith(a)):
            return False
        if registrar and (len(a) == 1) != (len(b) == 1):
            if len(left if len(a) == 1 else right) > 1:
                return False
    return True


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


def _extract_professor_given_names(professor_name: str) -> list[str]:
    """Given names and initials from a professor's stored name, in order."""
    if not professor_name:
        return []

    name = professor_name.strip()
    if "," in name:
        return _given_tokens(name.split(",", 1)[1])
    parts = name.split()
    if name.isupper():
        return _given_tokens(" ".join(parts[1:]))
    # "First Middle Last": everything but the last name (see _extract_professor_last_name)
    suffixes = {"jr", "jr.", "sr", "sr.", "ii", "iii", "iv", "phd", "ph.d."}
    if len(parts) >= 3 and parts[-1].lower() in suffixes:
        parts = parts[:-1]
    titles = {"DR", "PROF", "PROFESSOR", "MR", "MRS", "MS"}
    return [t for t in _given_tokens(" ".join(parts[:-1])) if t not in titles]


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
    department: str | None = None,
) -> MatchResult | None:
    """Match a parsed UCSB instructor name to an existing professor record.

    Parameters
    ----------
    parsed : ParsedInstructor
        The parsed instructor name from the UCSB API.
    professors : list[dict]
        Each dict must have keys: ``id``, ``name_rmp``, ``name_nexus``, and
        may have ``department``. Oldest first: among rows with the same name,
        the first one wins.
    department : str, optional
        The section's department code. When given, a professor whose stored
        name isn't the UCSB name must be in this department. Without it any
        department is accepted, as before.

    Returns
    -------
    MatchResult or None
        The best match, or None if no match meets the threshold or several
        different people fit equally well.
    """
    if not parsed or not professors:
        return None

    raw = _normalize_name(parsed.raw)
    for prof in professors:
        if _normalize_name(prof.get("name_nexus")) == raw:
            return MatchResult(
                professor_id=prof["id"],
                professor_name=prof["name_nexus"],
                confidence=1.0,
                match_method="exact",
            )

    # Score every (professor, stored name) pair; keep each professor's best.
    best: dict[int, tuple[float, str, str, dict]] = {}
    for prof in professors:
        if department and not _in_department(department, prof.get("department")):
            continue
        for name_field in ("name_rmp", "name_nexus"):
            prof_name = prof.get(name_field)
            if not prof_name:
                continue

            prof_last = _extract_professor_last_name(prof_name)
            if not prof_last:
                continue
            prof_given = _extract_professor_given_names(prof_name)
            both_given = bool(parsed.given) and bool(prof_given)
            registrar = prof_name.isupper()  # a Nexus or UCSB name, not an RMP one
            if both_given and not _given_names_agree(parsed.given, prof_given, registrar):
                continue

            if prof_last == parsed.last_name:
                score, method = (1.0, "exact") if both_given else (0.85, "exact")
            elif registrar:
                continue
            else:
                fuzzy_score = fuzz.ratio(prof_last, parsed.last_name)
                if fuzzy_score < FUZZY_THRESHOLD:
                    continue
                normalized = fuzzy_score / 100.0
                if both_given:
                    score, method = min(normalized + 0.1, 0.99), "fuzzy"
                else:
                    score, method = normalized * 0.8, "last_name_only"

            if score > best.get(prof["id"], (0.0,))[0]:
                best[prof["id"]] = (round(score, 2), method, prof_name, prof)

    top = max((entry[0] for entry in best.values()), default=0.0)
    if top < 0.6:
        logger.warning("No match found for instructor: %s", parsed.raw)
        return None

    # Rows sharing a Nexus name are one person (the oldest row wins); anything
    # else at the top score is a different person.
    people: dict[str, list[tuple]] = {}
    for prof_id, entry in best.items():
        if entry[0] == top:
            key = _normalize_name(entry[3].get("name_nexus")) or f"id:{prof_id}"
            people.setdefault(key, []).append((prof_id, entry))

    # A row with only an RMP name that fits as well as a Nexus-named row is
    # most likely the same person, not linked yet ("Olivia Henderson" and
    # HENDERSON O G, both English): the Nexus row, which has the grades, wins.
    nexus_named = {key: rows for key, rows in people.items() if not key.startswith("id:")}
    if nexus_named:
        people = nexus_named

    if len(people) > 1:
        logger.warning(
            "Ambiguous instructor %s: %d people fit (%s); not guessing",
            parsed.raw, len(people), ", ".join(sorted(people)),
        )
        return None

    prof_id, (score, method, prof_name, _prof) = min(next(iter(people.values())))
    return MatchResult(
        professor_id=prof_id,
        professor_name=prof_name,
        confidence=score,
        match_method=method,
    )

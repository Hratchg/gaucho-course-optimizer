"""Utilities for parsing and comparing Nexus professor names."""

import re


def parse_nexus_name(name: str) -> dict:
    """Parse a Nexus-format professor name into components.

    Handles formats:
      - "HUANG L"       -> {last: "huang", first: "l", is_initial: True}
      - "CHANG SHIYU"   -> {last: "chang", first: "shiyu", is_initial: False}
      - "SMITH, JOHN"   -> {last: "smith", first: "john", is_initial: False}
      - "SMITH, J"      -> {last: "smith", first: "j", is_initial: True}
      - "O'BRIEN SEAN"  -> {last: "o'brien", first: "sean", is_initial: False}
    """
    if not name or not name.strip():
        return {"last": "", "first": "", "is_initial": False}

    name = name.strip()

    # Comma-separated: "LAST, FIRST"
    if "," in name:
        parts = name.split(",", 1)
        last = parts[0].strip().lower()
        first = parts[1].strip().lower()
    else:
        # Space-separated: "LAST FIRST" — first token is last name
        # Handle multi-word last names with apostrophes: "O'BRIEN SEAN"
        tokens = name.split()
        if len(tokens) == 1:
            return {"last": tokens[0].lower(), "first": "", "is_initial": False}
        last = tokens[0].lower()
        first = " ".join(tokens[1:]).lower()

    is_initial = len(first) == 1 and first.isalpha()
    return {"last": last, "first": first, "is_initial": is_initial}


def is_initial_only(name: str) -> bool:
    """Check if a Nexus name has only an initial for the first name."""
    parsed = parse_nexus_name(name)
    return parsed["is_initial"]


def initial_matches(initial: str, rmp_first_name: str) -> bool:
    """Check if a single-letter initial matches an RMP first name's first letter."""
    if not initial or not rmp_first_name:
        return False
    return initial[0].lower() == rmp_first_name[0].lower()


def find_duplicate_pairs(
    names_with_dept: list[dict],
) -> list[tuple[dict, dict]]:
    """Find abbreviated + full name pairs in the same department.

    Each item in names_with_dept should have keys: id, name, department.
    Returns list of (abbreviated, full) tuples where:
      - Both share the same last name and department
      - One has an initial-only first name that matches the other's full first name
    """
    # Group by (last_name, department)
    from collections import defaultdict

    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for item in names_with_dept:
        parsed = parse_nexus_name(item["name"])
        key = (parsed["last"], (item.get("department") or "").lower())
        groups[key].append({**item, "_parsed": parsed})

    pairs = []
    for _key, members in groups.items():
        if len(members) < 2:
            continue

        initials = [m for m in members if m["_parsed"]["is_initial"]]
        fulls = [m for m in members if not m["_parsed"]["is_initial"] and m["_parsed"]["first"]]

        for abbr in initials:
            for full in fulls:
                if initial_matches(abbr["_parsed"]["first"], full["_parsed"]["first"]):
                    # Strip internal _parsed before returning
                    a = {k: v for k, v in abbr.items() if k != "_parsed"}
                    f = {k: v for k, v in full.items() if k != "_parsed"}
                    pairs.append((a, f))

    return pairs

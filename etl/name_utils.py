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


def _common_prefix_len(left: str, right: str) -> int:
    length = 0
    for a, b in zip(left, right):
        if a != b:
            break
        length += 1
    return length


def _covers_fragments(fragments: list[str], tokens: list[str]) -> bool:
    """True when each fragment lines up with a distinct token.

    The first fragment must be a real prefix (min 4 chars). Later hyphen
    fragments may only share a 3-character prefix because the Nexus dump
    cuts names at ~13 characters mid-token (``CASTELLA-CABE`` vs
    ``Castellanos Cabrera``).
    """
    used: set[int] = set()
    for index, frag in enumerate(fragments):
        need = 4 if index == 0 else 3
        if len(frag) < need:
            return False
        found = None
        for i, tok in enumerate(tokens):
            if i in used:
                continue
            if tok.startswith(frag) or _common_prefix_len(frag, tok) >= need:
                found = i
                break
        if found is None:
            return False
        used.add(found)
    return True


def truncated_name_match(nexus_name: str, rmp_name: str) -> bool:
    """True when a truncated Nexus name is a prefix of the RMP name tokens.

    Handles hyphenated surname fragments that the Nexus dump cuts off
    (``CASTELLA-CABE`` vs ``Ana Castellanos Cabrera``) and first/last
    pairs where the given name is also truncated (``ALONSO RODRIG`` vs
    ``Maria Alonso Rodriguez``). Single-token last-only names are rejected
    so ``WANG`` does not match ``Wangari``.
    """
    parsed = parse_nexus_name(nexus_name)
    if parsed["is_initial"]:
        return False

    last_parts = [p for p in parsed["last"].replace("-", " ").split() if p]
    first_parts = [
        p for p in parsed["first"].replace("-", " ").split() if p and len(p) > 1
    ]
    rmp_tokens = [
        t.lower().strip(".,")
        for t in (rmp_name or "").replace("-", " ").split()
        if t.strip()
    ]
    if not last_parts or not rmp_tokens:
        return False

    if len(last_parts) >= 2:
        return _covers_fragments(last_parts, rmp_tokens)

    if first_parts:
        return _covers_fragments(last_parts, rmp_tokens) and _covers_fragments(
            first_parts, rmp_tokens
        )

    return False


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

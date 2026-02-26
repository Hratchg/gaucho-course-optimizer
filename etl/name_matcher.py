import re
from thefuzz import fuzz

TITLE_PATTERNS = re.compile(r"\b(dr|prof|professor|mr|ms|mrs|phd|md)\b\.?", re.IGNORECASE)


def normalize_nexus_name(name: str) -> str:
    """Convert 'LAST, FIRST' to normalized 'first last'."""
    parts = name.split(",", 1)
    if len(parts) == 2:
        last, first = parts[0].strip(), parts[1].strip()
        name = f"{first} {last}"
    name = TITLE_PATTERNS.sub("", name)
    return " ".join(name.lower().split())


def normalize_rmp_name(name: str) -> str:
    """Convert 'First Last' to normalized 'first last'."""
    name = TITLE_PATTERNS.sub("", name)
    return " ".join(name.lower().split())


def match_confidence(name_a: str, name_b: str) -> int:
    """Return fuzzy match confidence (0-100) using token_sort_ratio."""
    return fuzz.token_sort_ratio(name_a, name_b)


def match_names(
    nexus_names: list[str],
    rmp_names: list[str],
    auto_threshold: int = 85,
    review_threshold: int = 70,
) -> dict:
    """Match Nexus names to RMP names.

    Returns dict: {nexus_name: {"rmp_name": str, "confidence": int, "status": str}}
    status is "auto" (>=85), "review" (70-84), or absent if <70.
    """
    matches = {}
    normalized_rmp = [(name, normalize_rmp_name(name)) for name in rmp_names]

    for nexus_name in nexus_names:
        norm_nexus = normalize_nexus_name(nexus_name)
        best_score = 0
        best_rmp_raw = None

        for rmp_raw, norm_rmp in normalized_rmp:
            score = match_confidence(norm_nexus, norm_rmp)
            if score > best_score:
                best_score = score
                best_rmp_raw = rmp_raw

        if best_score >= auto_threshold:
            matches[nexus_name] = {
                "rmp_name": best_rmp_raw,
                "confidence": best_score,
                "status": "auto",
            }
        elif best_score >= review_threshold:
            matches[nexus_name] = {
                "rmp_name": best_rmp_raw,
                "confidence": best_score,
                "status": "review",
            }

    return matches

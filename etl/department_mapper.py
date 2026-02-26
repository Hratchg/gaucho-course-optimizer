"""Map Nexus department codes to RMP department names and vice versa."""

from thefuzz import fuzz

# Nexus dept code -> RMP department name(s)
# Built from UCSB's department list and common RMP naming
DEPT_MAP: dict[str, list[str]] = {
    "ANTH": ["Anthropology"],
    "ART": ["Art", "Art Studio"],
    "ARTHI": ["Art History", "History Of Art And Architecture"],
    "ARTST": ["Art Studio"],
    "ASTRO": ["Astronomy", "Physics"],
    "BIOE": ["Bioengineering"],
    "BIOL": ["Biology", "Biological Sciences"],
    "BMSE": ["Biomolecular Science And Engineering"],
    "BL ST": ["Black Studies"],
    "CH E": ["Chemical Engineering"],
    "CHEM": ["Chemistry", "Chemistry And Biochemistry"],
    "CHIN": ["Chinese"],
    "CLASS": ["Classics"],
    "COMM": ["Communication"],
    "CMPSC": ["Computer Science"],
    "CMPTG": ["Computing"],
    "CNCSP": ["Counseling, Clinical & School Psychology"],
    "DANCE": ["Dance"],
    "DYNS": ["Dynamical Neuroscience"],
    "EARTH": ["Earth Science"],
    "EACS": ["East Asian Cultural Studies"],
    "ECON": ["Economics"],
    "ED": ["Education"],
    "ECE": ["Electrical And Computer Engineering", "Electrical Engineering"],
    "ENGL": ["English"],
    "ENGR": ["Engineering"],
    "ENV S": ["Environmental Studies"],
    "ESM": ["Environmental Science And Management"],
    "ES": ["Ethnic Studies"],
    "FAMST": ["Film And Media Studies"],
    "FEMST": ["Feminist Studies"],
    "FR": ["French", "French And Italian"],
    "GEOG": ["Geography"],
    "GER": ["German", "Germanic And Slavic Studies"],
    "GPS": ["Global Studies", "Global & International Studies"],
    "GREEK": ["Classics"],
    "HIST": ["History"],
    "INT": ["Interdisciplinary"],
    "ITAL": ["Italian", "French And Italian"],
    "JAPAN": ["Japanese"],
    "KOR": ["Korean"],
    "LATIN": ["Classics"],
    "LAIS": ["Latin American And Iberian Studies"],
    "LING": ["Linguistics"],
    "LIT": ["Comparative Literature", "Literature"],
    "MARSC": ["Marine Science"],
    "MATRL": ["Materials"],
    "MATH": ["Mathematics"],
    "ME": ["Mechanical Engineering"],
    "MAT": ["Media Arts And Technology"],
    "MCDB": ["Molecular, Cellular & Developmental Biology", "Biology"],
    "MUS": ["Music"],
    "PHIL": ["Philosophy"],
    "PHYS": ["Physics"],
    "POL S": ["Political Science"],
    "PORT": ["Portuguese"],
    "PSTAT": ["Statistics And Applied Probability", "Statistics"],
    "PSY": ["Psychology", "Psychological & Brain Sciences"],
    "RG ST": ["Religious Studies"],
    "RENST": ["Renaissance Studies"],
    "SLAV": ["Slavic Languages And Literature", "Germanic And Slavic Studies"],
    "SOC": ["Sociology"],
    "SPAN": ["Spanish", "Spanish And Portuguese"],
    "SHS": ["Society And Health Sciences"],
    "TMP": ["Technology Management"],
    "THTR": ["Theater", "Theater And Dance"],
    "WRIT": ["Writing"],
    "W&L": ["Writing And Literature"],
}

# Build reverse map: lowercase RMP name -> list of Nexus codes
_REVERSE_MAP: dict[str, list[str]] = {}
for code, rmp_names in DEPT_MAP.items():
    for rmp_name in rmp_names:
        key = rmp_name.lower()
        if key not in _REVERSE_MAP:
            _REVERSE_MAP[key] = []
        _REVERSE_MAP[key].append(code)


def departments_match(nexus_dept: str | None, rmp_dept: str | None) -> bool:
    """Check if a Nexus department code and an RMP department name refer to the same dept.

    Uses static map first, then fuzzy fallback (threshold 80).
    """
    if not nexus_dept or not rmp_dept:
        return False

    nexus_upper = nexus_dept.strip().upper()
    rmp_lower = rmp_dept.strip().lower()

    # Direct lookup: Nexus code -> known RMP names
    if nexus_upper in DEPT_MAP:
        for known_rmp in DEPT_MAP[nexus_upper]:
            if known_rmp.lower() == rmp_lower:
                return True

    # Reverse lookup: RMP name -> known Nexus codes
    if rmp_lower in _REVERSE_MAP:
        if nexus_upper in _REVERSE_MAP[rmp_lower]:
            return True

    # Fuzzy fallback: compare the Nexus code expansion against the RMP name
    if nexus_upper in DEPT_MAP:
        for known_rmp in DEPT_MAP[nexus_upper]:
            if fuzz.ratio(known_rmp.lower(), rmp_lower) >= 80:
                return True

    return False

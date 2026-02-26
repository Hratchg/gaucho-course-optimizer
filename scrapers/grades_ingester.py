import pandas as pd

GPA_SCALE = {
    "a_plus": 4.0, "a": 4.0, "a_minus": 3.7,
    "b_plus": 3.3, "b": 3.0, "b_minus": 2.7,
    "c_plus": 2.3, "c": 2.0, "c_minus": 1.7,
    "d_plus": 1.3, "d": 1.0, "d_minus": 0.7,
    "f": 0.0,
}

GRADE_COLUMNS = list(GPA_SCALE.keys())

# Mapping from Daily Nexus CSV column names to our internal schema
_CSV_COLUMN_MAP = {
    "Ap": "a_plus", "A": "a", "Am": "a_minus",
    "Bp": "b_plus", "B": "b", "Bm": "b_minus",
    "Cp": "c_plus", "C": "c", "Cm": "c_minus",
    "Dp": "d_plus", "D": "d", "Dm": "d_minus",
    "F": "f",
}


def normalize_course_code(code: str) -> str:
    """Remove all whitespace from a course code."""
    return "".join(code.split())


def compute_avg_gpa(row: dict) -> float:
    """Compute average GPA from grade counts (fallback/verification)."""
    total_points = 0.0
    total_students = 0
    for grade, points in GPA_SCALE.items():
        count = row.get(grade, 0)
        total_points += count * points
        total_students += count
    if total_students == 0:
        return 0.0
    return round(total_points / total_students, 2)


def parse_grades_csv(path: str) -> pd.DataFrame:
    """Parse the Daily Nexus courseGrades.csv.

    Maps raw CSV columns to our internal schema:
    - course → course_code (normalized, no spaces)
    - instructor → instructor
    - quarter, year → kept as-is
    - Ap/A/Am/Bp/B/Bm/Cp/C/Cm/Dp/D/Dm/F → a_plus/a/a_minus/.../f
    - avgGPA → avg_gpa
    - dept → department
    """
    df = pd.read_csv(path)

    # Rename grade columns from CSV format to our schema
    rename_map = {**_CSV_COLUMN_MAP}
    rename_map["avgGPA"] = "avg_gpa"
    rename_map["dept"] = "department"
    df = df.rename(columns=rename_map)

    # Normalize course codes
    df["course_code"] = df["course"].apply(normalize_course_code)

    # Fill NaN grade columns with 0
    for col in GRADE_COLUMNS:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(int)

    return df


def fetch_grades_csv(url: str = None) -> pd.DataFrame:
    """Fetch courseGrades.csv from GitHub and parse it."""
    if url is None:
        url = "https://raw.githubusercontent.com/dailynexusdata/grades-data/main/courseGrades.csv"
    return parse_grades_csv(url)

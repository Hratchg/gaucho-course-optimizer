import os
import pandas as pd
from scrapers.grades_ingester import parse_grades_csv, compute_avg_gpa, normalize_course_code


def test_normalize_course_code():
    assert normalize_course_code("PSTAT 120A") == "PSTAT120A"
    assert normalize_course_code("CMPSC   8") == "CMPSC8"
    assert normalize_course_code("ECON 1") == "ECON1"


def test_compute_avg_gpa():
    # 10 students all got A (4.0)
    row = {"a_plus": 0, "a": 10, "a_minus": 0, "b_plus": 0, "b": 0,
           "b_minus": 0, "c_plus": 0, "c": 0, "c_minus": 0,
           "d_plus": 0, "d": 0, "d_minus": 0, "f": 0}
    assert compute_avg_gpa(row) == 4.0

    # 5 A, 5 F → avg 2.0
    row2 = {**row, "a": 5, "f": 5}
    assert compute_avg_gpa(row2) == 2.0


def test_parse_grades_csv():
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "sample_grades.csv")
    df = parse_grades_csv(fixture_path)
    assert len(df) > 0
    assert "course_code" in df.columns
    assert "avg_gpa" in df.columns
    assert "instructor" in df.columns
    # Course codes should have no spaces
    for code in df["course_code"]:
        assert " " not in code

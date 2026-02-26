"""Tests for etl/department_mapper.py — department code/name matching."""

from etl.department_mapper import departments_match, DEPT_MAP


class TestDepartmentsMatch:
    def test_exact_match(self):
        assert departments_match("CMPSC", "Computer Science") is True

    def test_case_insensitive(self):
        assert departments_match("cmpsc", "computer science") is True

    def test_no_match(self):
        assert departments_match("CMPSC", "Mathematics") is False

    def test_empty_inputs(self):
        assert departments_match("", "Computer Science") is False
        assert departments_match("CMPSC", "") is False
        assert departments_match(None, "Computer Science") is False

    def test_fuzzy_fallback(self):
        # "Statistics" should fuzzy-match against "Statistics And Applied Probability"
        # but "Statistics" alone is also in the map for PSTAT
        assert departments_match("PSTAT", "Statistics") is True

    def test_multi_name_dept(self):
        # CHEM maps to both "Chemistry" and "Chemistry And Biochemistry"
        assert departments_match("CHEM", "Chemistry") is True
        assert departments_match("CHEM", "Chemistry And Biochemistry") is True

    def test_unknown_nexus_code(self):
        assert departments_match("ZZZZZ", "Computer Science") is False


class TestDeptMapCompleteness:
    def test_common_depts_present(self):
        for code in ["CMPSC", "MATH", "PHYS", "ECON", "ENGL", "HIST", "PSTAT", "PSY"]:
            assert code in DEPT_MAP, f"{code} missing from DEPT_MAP"

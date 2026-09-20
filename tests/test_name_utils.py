"""Tests for etl/name_utils.py — Nexus name parsing utilities."""

from etl.name_utils import (
    parse_nexus_name,
    is_initial_only,
    initial_matches,
    find_duplicate_pairs,
    truncated_name_match,
)


class TestParseNexusName:
    def test_initial_only_space(self):
        result = parse_nexus_name("HUANG L")
        assert result == {"last": "huang", "first": "l", "is_initial": True}

    def test_full_name_space(self):
        result = parse_nexus_name("CHANG SHIYU")
        assert result == {"last": "chang", "first": "shiyu", "is_initial": False}

    def test_comma_format(self):
        result = parse_nexus_name("SMITH, JOHN")
        assert result == {"last": "smith", "first": "john", "is_initial": False}

    def test_comma_initial(self):
        result = parse_nexus_name("SMITH, J")
        assert result == {"last": "smith", "first": "j", "is_initial": True}

    def test_single_token(self):
        result = parse_nexus_name("JONES")
        assert result == {"last": "jones", "first": "", "is_initial": False}

    def test_empty_string(self):
        result = parse_nexus_name("")
        assert result == {"last": "", "first": "", "is_initial": False}


class TestTruncatedNameMatch:
    def test_hyphenated_surname_fragments(self):
        assert truncated_name_match("CASTELLA-CABE", "Ana Castellanos Cabrera") is True

    def test_truncated_given_and_last(self):
        assert truncated_name_match("ALONSO RODRIG", "Maria Alonso Rodriguez") is True

    def test_does_not_match_unrelated_short_last(self):
        assert truncated_name_match("WANG", "Wangari Maathai") is False

    def test_rejects_initial_only(self):
        assert truncated_name_match("CHANG S", "Shiyu Chang") is False


class TestIsInitialOnly:
    def test_initial(self):
        assert is_initial_only("HUANG L") is True

    def test_full_name(self):
        assert is_initial_only("CHANG SHIYU") is False


class TestInitialMatches:
    def test_match(self):
        assert initial_matches("s", "Shiyu") is True

    def test_no_match(self):
        assert initial_matches("j", "Shiyu") is False

    def test_empty(self):
        assert initial_matches("", "Shiyu") is False
        assert initial_matches("s", "") is False


class TestFindDuplicatePairs:
    def test_finds_pair(self):
        names = [
            {"id": 1, "name": "CHANG S", "department": "CMPSC"},
            {"id": 2, "name": "CHANG SHIYU", "department": "CMPSC"},
        ]
        pairs = find_duplicate_pairs(names)
        assert len(pairs) == 1
        abbr, full = pairs[0]
        assert abbr["id"] == 1
        assert full["id"] == 2

    def test_different_dept_no_pair(self):
        names = [
            {"id": 1, "name": "CHANG S", "department": "CMPSC"},
            {"id": 2, "name": "CHANG SHIYU", "department": "MATH"},
        ]
        pairs = find_duplicate_pairs(names)
        assert len(pairs) == 0

    def test_no_initial_no_pair(self):
        names = [
            {"id": 1, "name": "CHANG SHIYU", "department": "CMPSC"},
            {"id": 2, "name": "CHANG ALICE", "department": "CMPSC"},
        ]
        pairs = find_duplicate_pairs(names)
        assert len(pairs) == 0

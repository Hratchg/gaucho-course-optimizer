"""Tests for etl/name_utils.py — Nexus name parsing utilities."""

from etl.name_utils import (
    parse_nexus_name,
    is_initial_only,
    initial_matches,
    find_duplicate_pairs,
    truncated_name_match,
    given_name_conflict,
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


class TestGivenNameConflict:
    """Links seen wrong in production (docs/audits/2026-09-29-rmp-link-audit.md)."""

    # Nexus gives initials and the RMP first name starts with none of them.
    def test_first_initial_conflict(self):
        assert given_name_conflict("YANG M", "Tao", "Yang") is True

    def test_conflicts_with_every_initial(self):
        assert given_name_conflict("SWEENEY S H", "Ed", "Sweeney") is True
        assert given_name_conflict("CHANG A Y", "Shiyu", "Chang") is True
        assert given_name_conflict("BERGSTROM R E", "Ted", "Bergstrom") is True

    def test_surname_first_rmp_profile_conflicts(self):
        # "Chen Ji" scored 92 against CHEN J only because token_sort ignores order.
        assert given_name_conflict("CHEN J", "Chen", "Ji") is True

    def test_rmp_profile_without_a_given_name_conflicts(self):
        assert given_name_conflict("WALKER Z", "DR", "Walker") is True
        assert given_name_conflict("MULFINGER J", ".", "Mulfinger") is True
        assert given_name_conflict("WALKER Z", "", "Walker") is True

    # Legitimate matches that must keep working.
    def test_first_initial_matches(self):
        assert given_name_conflict("BERGSTROM T C", "Ted", "Bergstrom") is False
        assert given_name_conflict("HUANG L", "Lei", "Huang") is False

    def test_middle_initial_matches(self):
        # "SMITH J R" going by Robert, "ZIMMERMAN E D" going by Don.
        assert given_name_conflict("SMITH J R", "Robert", "Smith") is False
        assert given_name_conflict("ZIMMERMAN E D", "Don", "Zimmerman") is False
        assert given_name_conflict("SMITH, J R", "Robert", "Smith") is False

    def test_rmp_initials_and_punctuation(self):
        assert given_name_conflict("HAWKER C J", "C. J.", "Hawker") is False
        assert given_name_conflict("HAWKER C J", "Dr. Craig", "Hawker") is False

    def test_full_given_name_matches(self):
        assert given_name_conflict("CONRAD, PHILL", "Phill", "Conrad") is False
        assert given_name_conflict("WANG YUXIANG", "Yu-Xiang", "Wang") is False
        assert given_name_conflict("FOUQUE J-P", "Jean-Pierre", "Fouque") is False

    def test_full_given_name_conflict(self):
        assert given_name_conflict("CHANG YU-CHI", "Shiyu", "Chang") is True
        assert given_name_conflict("ZHAO LIANG", "Xiaojian", "Zhao") is True

    def test_full_given_name_middle_name_matches(self):
        assert given_name_conflict("SMITH JOHN R", "Robert", "Smith") is False

    def test_second_token_that_is_really_surname(self):
        # Nexus cuts names at 13 characters and has no given name for these.
        assert given_name_conflict("RAMIREZ MENDE", "Maria", "Ramirez Mendez") is False
        assert given_name_conflict("ALVES FERREIR", "Aline", "Ferreira") is False
        assert given_name_conflict("ARVIZU RAMIRE", "Aharon", "Arvizu Ramírez") is False
        assert given_name_conflict("DE TOMASO A W", "Anthony", "De Tomaso") is False
        assert given_name_conflict("VAN DE WALLE", "Chris", "Van De Walle") is False

    def test_surname_first_storage_with_full_given_name(self):
        assert given_name_conflict("ZHANG LIMING", "Zhang", "Liming") is False

    def test_no_given_name_on_nexus(self):
        assert given_name_conflict("CASTELLA-CABE", "Ana", "Castellanos Cabrera") is False
        assert given_name_conflict("HUANG", "Lei", "Huang") is False


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

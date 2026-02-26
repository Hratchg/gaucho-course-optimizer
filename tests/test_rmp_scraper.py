import json
import os
from scrapers.rmp_scraper import parse_teacher_node, RmpScraper


def _load_fixture():
    path = os.path.join(os.path.dirname(__file__), "fixtures", "rmp_graphql_response.json")
    with open(path) as f:
        return json.load(f)


def test_parse_teacher_node():
    fixture = _load_fixture()
    node = fixture["data"]["newSearch"]["teachers"]["edges"][0]["node"]
    result = parse_teacher_node(node)

    assert result["legacy_id"] == 1234
    assert result["first_name"] == "John"
    assert result["last_name"] == "Smith"
    assert result["department"] == "Statistics"
    assert result["avg_rating"] == 4.2
    assert result["avg_difficulty"] == 3.1
    assert result["would_take_again_pct"] == 85.0
    assert result["num_ratings"] == 42
    assert len(result["comments"]) == 2
    assert "clear lectures" in result["comments"][0]["text"]


def test_scraper_uses_school_id():
    scraper = RmpScraper(school_id=1077)
    assert scraper.school_id == 1077
    assert scraper.school_id_encoded == "U2Nob29sLTEwNzc="


def _load_name_search_fixture():
    path = os.path.join(os.path.dirname(__file__), "fixtures", "rmp_name_search_response.json")
    with open(path) as f:
        return json.load(f)


def test_search_teacher_by_name_parses_results():
    """search_teacher_by_name returns parsed teacher dicts from name search results."""
    from scrapers.rmp_scraper import NAME_SEARCH_QUERY
    assert "$text" in NAME_SEARCH_QUERY
    assert "$schoolID" in NAME_SEARCH_QUERY

    fixture = _load_name_search_fixture()
    edges = fixture["data"]["newSearch"]["teachers"]["edges"]
    results = [parse_teacher_node(e["node"]) for e in edges]

    assert len(results) == 2
    assert results[0]["first_name"] == "John"
    assert results[0]["last_name"] == "Smith"
    assert results[0]["legacy_id"] == 5555
    assert len(results[0]["comments"]) == 2
    assert results[1]["legacy_id"] == 6666
    assert len(results[1]["comments"]) == 0

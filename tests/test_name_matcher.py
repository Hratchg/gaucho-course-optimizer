from etl.name_matcher import normalize_nexus_name, normalize_rmp_name, match_names, match_confidence


def test_normalize_nexus_name():
    assert normalize_nexus_name("SMITH, JOHN") == "john smith"
    assert normalize_nexus_name("DE LA CRUZ, MARIA") == "maria de la cruz"
    assert normalize_nexus_name("O'BRIEN, PATRICK") == "patrick o'brien"


def test_normalize_rmp_name():
    assert normalize_rmp_name("John Smith") == "john smith"
    assert normalize_rmp_name("Dr. Maria De La Cruz") == "maria de la cruz"


def test_match_confidence_exact():
    score = match_confidence("john smith", "john smith")
    assert score == 100


def test_match_confidence_reordered():
    score = match_confidence("john smith", "smith john")
    assert score >= 85


def test_match_confidence_partial():
    score = match_confidence("john smith", "j smith")
    assert 50 < score < 100


def test_match_names_auto_links():
    nexus_names = ["SMITH, JOHN", "DOE, JANE"]
    rmp_names = ["John Smith", "Jane Doe"]
    matches = match_names(nexus_names, rmp_names)
    assert matches["SMITH, JOHN"]["rmp_name"] == "John Smith"
    assert matches["SMITH, JOHN"]["confidence"] >= 85
    assert matches["DOE, JANE"]["rmp_name"] == "Jane Doe"


def test_match_names_no_match():
    nexus_names = ["ZHANG, WEI"]
    rmp_names = ["Robert Johnson"]
    matches = match_names(nexus_names, rmp_names)
    assert "ZHANG, WEI" not in matches or matches["ZHANG, WEI"]["confidence"] < 70

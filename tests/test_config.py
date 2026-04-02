from api.config import Settings


def test_allowed_origins_parses_comma_separated_string():
    s = Settings(allowed_origins="https://example.com,http://localhost:5173")
    assert s.get_origins() == ["https://example.com", "http://localhost:5173"]


def test_allowed_origins_single_origin():
    s = Settings(allowed_origins="https://example.com")
    assert s.get_origins() == ["https://example.com"]


def test_allowed_origins_strips_whitespace():
    s = Settings(allowed_origins="https://a.com , https://b.com")
    assert s.get_origins() == ["https://a.com", "https://b.com"]


def test_allowed_origins_default_when_not_set():
    s = Settings(_env_file=None)
    assert s.get_origins() == ["http://localhost:5173", "http://localhost:3000"]


def test_allowed_origins_filters_empty_segments():
    s = Settings(allowed_origins="https://a.com,,https://b.com")
    assert s.get_origins() == ["https://a.com", "https://b.com"]

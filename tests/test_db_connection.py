from db.connection import get_engine, get_session


def test_get_engine_returns_engine():
    engine = get_engine()
    assert engine is not None
    assert "postgresql" in str(engine.url)


def test_get_session_returns_session():
    session = get_session()
    assert session is not None
    session.close()

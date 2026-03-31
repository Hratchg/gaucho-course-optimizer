from db.connection import get_engine, get_session, get_session_local


def test_get_engine_returns_engine():
    engine = get_engine()
    assert engine is not None
    assert "postgresql" in str(engine.url)


def test_get_session_returns_session():
    session = get_session()
    assert session is not None
    session.close()


def test_get_session_local_returns_singleton():
    factory1 = get_session_local()
    factory2 = get_session_local()
    assert factory1 is factory2


def test_get_session_local_cold_start():
    """get_session_local() works when called before get_engine() (no deadlock)."""
    import db.connection as conn
    conn._engine = None
    conn._SessionLocal = None
    factory = conn.get_session_local()
    assert factory is not None
    assert conn._engine is not None  # engine initialized as side effect

from collections.abc import Generator
from sqlalchemy.orm import Session
from db.connection import get_session_local


def get_db() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session for the duration of one HTTP request.

    Uses the shared session factory from db/connection.py — do NOT call
    create_engine() here. Pool config (pool_size=5, max_overflow=10,
    pool_recycle=1800, pool_pre_ping=True) is already set on the engine.
    """
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

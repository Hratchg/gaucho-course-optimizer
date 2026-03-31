import os
import threading
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_engine = None
_SessionLocal = None
_lock = threading.Lock()


def get_engine():
    global _engine
    if _engine is None:
        with _lock:
            if _engine is None:
                url = os.environ.get("DATABASE_URL", "postgresql://gco:gco@localhost:5432/gco")
                _engine = create_engine(
                    url,
                    pool_size=5,
                    max_overflow=10,
                    pool_recycle=1800,
                    pool_pre_ping=True,
                )
    return _engine


# Phase 2 FastAPI usage:
#   from db.connection import get_session_local
#   SessionLocal = get_session_local()  # not: from db.connection import SessionLocal
def get_session_local():
    global _SessionLocal
    if _SessionLocal is None:
        with _lock:
            if _SessionLocal is None:
                _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


def get_session():
    Session = get_session_local()
    return Session()

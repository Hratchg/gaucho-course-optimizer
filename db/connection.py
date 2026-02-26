import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        url = os.environ.get("DATABASE_URL", "postgresql://gco:gco@localhost:5432/gco")
        _engine = create_engine(url, pool_pre_ping=True)
    return _engine


def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()

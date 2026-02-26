import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "postgresql://gco:gco@localhost:5432/gco_test")

from db.models import Base
from db.connection import get_engine


@pytest.fixture(scope="session")
def engine():
    eng = get_engine()
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def db_session(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

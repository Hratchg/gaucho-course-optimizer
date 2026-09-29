import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Load .env if present so DATABASE_URL is available without manual env injection.
# setdefault ensures that an already-set DATABASE_URL (e.g. from CI env) wins.
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"), override=False)
except ImportError:
    pass  # python-dotenv not installed; rely on environment

os.environ.setdefault("DATABASE_URL", "postgresql://gco:gco@localhost:5432/gco_test")
os.environ.setdefault("RATE_LIMIT_ENABLED", "0")

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
    """Create a transactional session that rolls back after each test.

    The session joins an outer connection-level transaction with
    join_transaction_mode="create_savepoint" (the SQLAlchemy 2.x recipe), so
    session.commit() only releases a SAVEPOINT and everything is rolled back
    at the end. Unlike the old "restart the savepoint after every commit"
    listener, this also lets code under test use session.begin_nested().
    """
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection, join_transaction_mode="create_savepoint")
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()

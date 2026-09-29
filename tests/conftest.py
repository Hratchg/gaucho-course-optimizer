import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tests.db_guard import ALLOW_REMOTE_ENV, remote_database_error

# DATABASE_URL comes from the environment only, never from .env: .env holds the
# app's own database (.env.example is a Neon URL), and the session fixture
# below drops every table. CI sets DATABASE_URL; locally, pass it explicitly.
os.environ.setdefault("DATABASE_URL", "postgresql://gco:gco@localhost:5432/gco_test")
os.environ.setdefault("RATE_LIMIT_ENABLED", "0")

from db.models import Base
from db.connection import get_engine


def pytest_configure(config):
    """Stop before collection, and so before any engine exists, on a remote DATABASE_URL."""
    refusal = remote_database_error(
        os.environ["DATABASE_URL"], allow_remote=os.environ.get(ALLOW_REMOTE_ENV) == "1"
    )
    if refusal:
        raise pytest.UsageError(refusal)


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

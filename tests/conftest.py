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
    """Create a transactional session that rolls back after each test.

    Uses the nested-transaction (SAVEPOINT) pattern so that even explicit
    session.commit() calls inside tests are contained and rolled back.
    """
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    # Start a SAVEPOINT — session.commit() will release *this* savepoint,
    # not the outer transaction, so we can still roll everything back.
    nested = connection.begin_nested()

    # After every commit, re-open a new SAVEPOINT so subsequent operations
    # within the same test keep working inside the outer transaction.
    from sqlalchemy import event

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        if trans.nested and not trans._parent.nested:
            sess.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()

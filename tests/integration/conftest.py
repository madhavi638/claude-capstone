"""Integration-test fixtures.

Requires a running Postgres reachable via the HMS6_DB_* env vars (see
database/docker-compose.yml):

    docker compose -f database/docker-compose.yml up -d

Each test runs inside an outer transaction that is rolled back on teardown,
so tests never leave data behind even though the code under test calls
session.commit() internally (standard SQLAlchemy join-into-external-
transaction pattern).
"""

import uuid

import pytest
from sqlalchemy import event
from sqlalchemy.orm import Session

from backend.database import Base, engine
from backend.models.patient import Patient
from backend.models.provider import Provider


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def db_session():
    connection = engine.connect()
    outer_transaction = connection.begin()
    session = Session(bind=connection)
    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess, transaction):
        if transaction.nested and not transaction._parent.nested:
            sess.begin_nested()

    yield session

    session.close()
    outer_transaction.rollback()
    connection.close()


@pytest.fixture()
def patient(db_session) -> Patient:
    p = Patient(full_name="Test Patient")
    db_session.add(p)
    db_session.flush()
    return p


@pytest.fixture()
def provider(db_session) -> Provider:
    p = Provider(full_name="Test Provider", specialty="General")
    db_session.add(p)
    db_session.flush()
    return p


@pytest.fixture()
def staff_actor_id() -> uuid.UUID:
    return uuid.uuid4()

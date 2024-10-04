# ruff: noqa
import pytest
import sqlalchemy as sa
from pytest_docker_service import docker_container
from sqlalchemy.orm import Session


from djgram.db.sqlalchemyv2_nested_mutable.tests.config import settings
from djgram.db.sqlalchemyv2_nested_mutable.tests.utils import wait_pg_ready

container = docker_container(
    scope="session",
    image_name=settings.POSTGRES_IMAGE_NAME,
    container_name=settings.POSTGRES_CONTAINER_NAME,
    ports={settings.POSTGRES_PORT: settings.POSTGRES_FWD_PORT},
    environment={
        "POSTGRES_USER": settings.POSTGRES_USER,
        "POSTGRES_PASSWORD": settings.POSTGRES_PASSWORD,
        "POSTGRES_DB": settings.POSTGRES_DB,
    },
)


@pytest.fixture(scope="session")
def pg_dbinfo(container):
    port = container.port_map[settings.POSTGRES_PORT]
    port = int(port[0] if isinstance(port, list) else port)
    dbinfo = {
        "port": port,
        "host": settings.POSTGRES_HOST,
        "user": settings.POSTGRES_USER,
        "password": settings.POSTGRES_PASSWORD,
        "database": settings.POSTGRES_DB,
        "echo": settings.POSTGRES_ECHO,
    }
    wait_pg_ready(dbinfo)
    print(f"Prepared PostgreSQL: {dbinfo}")  # noqa: T201
    return dbinfo


from sqlalchemy import Connection, Engine, event


@pytest.fixture(scope="session")
def engine(pg_dbinfo):
    """
    Engine factory (used by tests)
    """
    return sa.create_engine(
        "postgresql://{user}:{password}@{host}:{port}/{database}".format(**pg_dbinfo), echo=pg_dbinfo["echo"]
    )


@pytest.fixture(scope="session")
def connection(engine: Engine):
    """
    Connection factory (used by tests)
    """
    with engine.connect() as connection:
        yield connection


@pytest.fixture(scope="module", autouse=True)
def setup_db(connection: Connection, mapper):
    """
    Create all tables as defined by the mapper fixture (which is defined in each set of tests)
    Tables are flushed to the db
    """
    mapper.metadata.create_all(connection)
    connection.commit()
    yield connection
    mapper.metadata.drop_all(connection)


@pytest.fixture(autouse=True)
def session(connection: Connection):
    """
    Session factory that wraps the session with a top-level transaction
    and then uses nested transactions (via SAVEPOINTs) to track and rollback ALL changes

    Note: if you want to inspect the contents of the tables for debugging, connect with pgAdmin and
    commit the nested transaction and outer transaction.
    """
    with connection.begin() as transaction:
        with Session(bind=connection) as session:
            nested = connection.begin_nested()

            @event.listens_for(session, "after_transaction_end")
            def restart_savepoint(session, transaction) -> None:
                nonlocal nested

                if not nested._transaction_is_active():
                    nested = session.begin_nested()

            yield session

        # rollback ( and let this handle any savepoints to avoid error thrown by SA )
        # SAWarning: nested transaction already deassociated from connection)
        transaction.rollback()

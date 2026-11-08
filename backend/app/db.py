"""Database connection. Routes get a session with `db: Session = Depends(get_db)`."""

from fastapi import HTTPException
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session

from app import config


class Base(DeclarativeBase):
    """Parent class of every table in models.py."""


_engine = None

# Time limits, so a database connection that silently dies can't make requests wait forever.
# (Without them, stuck requests pile up until the server stops answering anything.)
CONNECT_ARGS = {
    "connect_timeout": 10,  # seconds to open a connection
    "keepalives": 1,  # notice a dead connection: probe after 30 s of silence, every 10 s, give up after 3
    "keepalives_idle": 30,
    "keepalives_interval": 10,
    "keepalives_count": 3,
    "tcp_user_timeout": 30000,  # ms: give up when sent data is not acknowledged
}
STATEMENT_TIMEOUT_MS = 20000  # the slowest query (the analysis page) takes well under a second


def get_engine():
    # Created on first use, so the game still works before the database is set up.
    global _engine
    if _engine is None:
        if not config.DATABASE_URL:
            raise HTTPException(503, "The database is not set up yet (DATABASE_URL is missing in .env)")
        _engine = create_engine(
            config.DATABASE_URL,
            pool_pre_ping=True,  # test a connection before using it
            pool_recycle=600,  # replace connections older than 10 minutes
            pool_timeout=15,  # seconds to wait for a free connection, then answer with an error
            connect_args=CONNECT_ARGS,
        )

        @event.listens_for(_engine, "connect")
        def limit_query_time(connection, _record):
            with connection.cursor() as cursor:
                cursor.execute(f"SET statement_timeout = {STATEMENT_TIMEOUT_MS}")
            connection.commit()

    return _engine


def get_db():
    with Session(get_engine()) as session:
        yield session

"""Database connection. Routes get a session with `db: Session = Depends(get_db)`."""

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session

from app import config


class Base(DeclarativeBase):
    """Parent class of every table in models.py."""


_engine = None


def get_engine():
    # Created on first use, so the game still works before the database is set up.
    global _engine
    if _engine is None:
        if not config.DATABASE_URL:
            raise HTTPException(503, "The database is not set up yet (DATABASE_URL is missing in .env)")
        _engine = create_engine(config.DATABASE_URL, pool_pre_ping=True)
    return _engine


def get_db():
    with Session(get_engine()) as session:
        yield session

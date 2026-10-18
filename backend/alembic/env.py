"""Runs migrations. Alembic calls this file; you don't run it directly."""

from alembic import context
from sqlalchemy import create_engine

from app import config as app_config
from app import models  # noqa: F401  (loads the tables so Alembic knows about them)
from app.db import Base

target_metadata = Base.metadata


def run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


# The tests pass in their own database connection; otherwise use DATABASE_URL from .env
connection = context.config.attributes.get("connection")
if connection is not None:
    run_migrations(connection)
else:
    if not app_config.DATABASE_URL:
        raise SystemExit("DATABASE_URL is not set. Fill it in .env first (see .env.example).")
    with create_engine(app_config.DATABASE_URL).connect() as connection:
        run_migrations(connection)

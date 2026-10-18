"""Accounts: profiles, game sessions and answers

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

TABLES = ["profiles", "game_sessions", "answers", "alembic_version"]


def upgrade():
    op.create_table(
        "profiles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("username", sa.String(40), unique=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "game_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("mistakes", sa.Integer(), nullable=False),
        sa.Column("result", sa.String(10)),
        sa.Column("started_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("ended_at", sa.DateTime()),
    )
    op.create_index("ix_game_sessions_user_id", "game_sessions", ["user_id"])
    op.create_table(
        "answers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "session_id", sa.Integer(), sa.ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("mode", sa.Integer(), nullable=False),
        sa.Column("question_notes", postgresql.ARRAY(sa.String(4)), nullable=False),
        sa.Column("given_notes", postgresql.ARRAY(sa.String(4)), nullable=False),
        sa.Column("correct", sa.Boolean(), nullable=False),
        sa.Column("response_ms", sa.Integer()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_answers_session_id", "answers", ["session_id"])

    # Safety net for Supabase: with Row Level Security ON and no policies, the public
    # Supabase API (used with the anon key in browsers) can't read or change these tables.
    # Our backend connects as the table owner, so it isn't affected.
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")


def downgrade():
    op.drop_table("answers")
    op.drop_table("game_sessions")
    op.drop_table("profiles")

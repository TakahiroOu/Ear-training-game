"""Competitions, entries and their answers

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "competitions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("kind", sa.String(10), nullable=False),
        sa.Column("title", sa.String(60)),
        sa.Column("seed", sa.String(40), nullable=False, unique=True),
        sa.Column("question_count", sa.Integer(), nullable=False),
        sa.Column("starts_at", sa.DateTime(), nullable=False),
        sa.Column("ends_at", sa.DateTime(), nullable=False),
        sa.Column("join_code", sa.String(8), unique=True),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("profiles.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "competition_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "competition_id", sa.Integer(), sa.ForeignKey("competitions.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("next_index", sa.Integer(), nullable=False),
        sa.Column("question_served_at", sa.DateTime()),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("correct", sa.Integer(), nullable=False),
        sa.Column("total_ms", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime()),
        sa.UniqueConstraint("competition_id", "user_id"),
    )
    op.create_index("ix_competition_entries_competition_id", "competition_entries", ["competition_id"])
    op.create_index("ix_competition_entries_user_id", "competition_entries", ["user_id"])
    op.create_table(
        "competition_answers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "entry_id", sa.Integer(), sa.ForeignKey("competition_entries.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("index", sa.Integer(), nullable=False),
        sa.Column("mode", sa.Integer(), nullable=False),
        sa.Column("question_notes", postgresql.ARRAY(sa.String(4)), nullable=False),
        sa.Column("given_notes", postgresql.ARRAY(sa.String(4)), nullable=False),
        sa.Column("result", sa.String(10), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("response_ms", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("entry_id", "index"),
    )
    op.create_index("ix_competition_answers_entry_id", "competition_answers", ["entry_id"])
    for table in ["competitions", "competition_entries", "competition_answers"]:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")  # see 0001


def downgrade():
    op.drop_table("competition_answers")
    op.drop_table("competition_entries")
    op.drop_table("competitions")

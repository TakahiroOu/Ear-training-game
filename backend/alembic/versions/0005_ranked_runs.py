"""Ranked runs: categories, a seed per run, several runs per player; remove daily/weekly/monthly

Revision ID: 0005
Revises: 0004
"""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    # The time-limited contests are replaced by always-open ranked runs
    op.execute("DELETE FROM competitions WHERE kind IN ('daily', 'weekly', 'monthly')")
    op.add_column("competitions", sa.Column("category", sa.String(10), nullable=False, server_default="mixed"))
    op.add_column("competition_entries", sa.Column("seed", sa.String(40)))
    op.execute(
        "UPDATE competition_entries e SET seed = c.seed FROM competitions c WHERE c.id = e.competition_id"
    )
    op.alter_column("competition_entries", "seed", nullable=False)
    # Ranked: many runs per player. (Class competitions still allow one; that is checked in the code.)
    op.drop_constraint("competition_entries_competition_id_user_id_key", "competition_entries", type_="unique")


def downgrade():
    op.create_unique_constraint(
        "competition_entries_competition_id_user_id_key", "competition_entries", ["competition_id", "user_id"]
    )
    op.drop_column("competition_entries", "seed")
    op.drop_column("competitions", "category")

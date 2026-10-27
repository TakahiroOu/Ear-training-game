"""Each run has its own leaderboard name

Revision ID: 0007
Revises: 0006
"""

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("competition_entries", sa.Column("player_name", sa.String(20)))
    # Earlier runs keep the name their player had chosen
    op.execute(
        "UPDATE competition_entries e SET player_name = p.username "
        "FROM profiles p WHERE p.id = e.user_id"
    )


def downgrade():
    op.drop_column("competition_entries", "player_name")

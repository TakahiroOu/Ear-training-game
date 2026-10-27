"""Recalculate earlier runs under the new rule: wrong answers score 0

Revision ID: 0008
Revises: 0007
"""

from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade():
    # Give back the points that wrong answers took away, then set those answers to 0
    op.execute(
        "UPDATE competition_entries e SET score = e.score - lost.points "
        "FROM (SELECT entry_id, SUM(points) AS points FROM competition_answers "
        "      WHERE result = 'wrong' AND points < 0 GROUP BY entry_id) lost "
        "WHERE lost.entry_id = e.id"
    )
    op.execute("UPDATE competition_answers SET points = 0 WHERE result = 'wrong' AND points < 0")


def downgrade():
    pass  # the old minus points are not kept

"""Each run has its own number of questions

Revision ID: 0006
Revises: 0005
"""

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("competition_entries", sa.Column("question_count", sa.Integer()))
    op.execute(
        "UPDATE competition_entries e SET question_count = c.question_count "
        "FROM competitions c WHERE c.id = e.competition_id"
    )
    op.alter_column("competition_entries", "question_count", nullable=False)


def downgrade():
    op.drop_column("competition_entries", "question_count")

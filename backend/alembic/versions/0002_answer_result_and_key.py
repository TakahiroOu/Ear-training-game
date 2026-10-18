"""Answers: add result (right / octave / wrong) and key

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("answers", sa.Column("result", sa.String(10)))
    op.add_column("answers", sa.Column("key", sa.String(10)))
    # Answers saved before this change were only right or wrong
    op.execute("UPDATE answers SET result = CASE WHEN correct THEN 'right' ELSE 'wrong' END")
    op.alter_column("answers", "result", nullable=False)


def downgrade():
    op.drop_column("answers", "key")
    op.drop_column("answers", "result")

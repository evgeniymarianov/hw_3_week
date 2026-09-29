"""добавление счетчика просмотров мероприятий

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_views",
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id"), primary_key=True),
        sa.Column("views_count", sa.Integer(), server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_table("event_views")

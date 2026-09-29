"""create delivery analytics tables

Revision ID: 20260727_0002
Revises:
Create Date: 2026-07-27 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260727_0002"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "courier_tracking_points",
        sa.Column("courier_id", sa.String(length=128), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("order_id", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("darkstore_id", sa.String(length=128), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("courier_id", "recorded_at"),
    )
    op.create_index(
        op.f("ix_courier_tracking_points_darkstore_id"),
        "courier_tracking_points",
        ["darkstore_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_courier_tracking_points_order_id"),
        "courier_tracking_points",
        ["order_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_courier_tracking_points_status"),
        "courier_tracking_points",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_courier_tracking_points_status"),
        table_name="courier_tracking_points",
    )
    op.drop_index(
        op.f("ix_courier_tracking_points_order_id"),
        table_name="courier_tracking_points",
    )
    op.drop_index(
        op.f("ix_courier_tracking_points_darkstore_id"),
        table_name="courier_tracking_points",
    )
    op.drop_table("courier_tracking_points")

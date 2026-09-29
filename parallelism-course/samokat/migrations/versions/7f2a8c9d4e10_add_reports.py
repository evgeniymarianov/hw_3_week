"""add reports

Revision ID: 7f2a8c9d4e10
Revises: b20616432e0f
Create Date: 2026-07-20 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7f2a8c9d4e10"
down_revision: Union[str, Sequence[str], None] = "b20616432e0f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("file_path", sa.String(), nullable=True),
        sa.Column("error", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reports_status"), "reports", ["status"], unique=False)
    op.create_index(op.f("ix_reports_user_id"), "reports", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_reports_user_id"), table_name="reports")
    op.drop_index(op.f("ix_reports_status"), table_name="reports")
    op.drop_table("reports")

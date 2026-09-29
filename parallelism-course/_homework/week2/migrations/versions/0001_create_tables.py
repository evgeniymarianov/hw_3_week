"""создание всех таблиц

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

seat_status = postgresql.ENUM(
    "available", "reserved", "sold", name="seat_status", create_type=False
)
booking_status = postgresql.ENUM(
    "pending_payment",
    "paid",
    "cancelled",
    "expired",
    name="booking_status",
    create_type=False,
)


def upgrade() -> None:
    postgresql.ENUM("available", "reserved", "sold", name="seat_status").create(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(
        "pending_payment", "paid", "cancelled", "expired", name="booking_status"
    ).create(op.get_bind(), checkfirst=True)

    op.create_table(
        "locations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("city", sa.String(120), nullable=False),
        sa.Column("address", sa.String(500), nullable=False),
    )
    op.create_table(
        "seats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("location_id", sa.Integer(), sa.ForeignKey("locations.id"), nullable=False),
        sa.Column("sector", sa.String(80), nullable=False),
        sa.Column("row", sa.Integer(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("x", sa.Integer(), nullable=False),
        sa.Column("y", sa.Integer(), nullable=False),
        sa.UniqueConstraint("location_id", "sector", "row", "number", name="uq_seat_position"),
    )
    op.create_index("ix_seats_location_id", "seats", ["location_id"])
    op.create_index("ix_seats_sector", "seats", ["sector"])

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organizer_id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), sa.ForeignKey("locations.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.String(2000), nullable=True),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("starts_at", sa.DateTime(), nullable=False),
        sa.Column("base_price", sa.Integer(), nullable=False),
    )
    op.create_index("ix_events_organizer_id", "events", ["organizer_id"])
    op.create_index("ix_events_location_id", "events", ["location_id"])
    op.create_index("ix_events_starts_at", "events", ["starts_at"])

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("payment_commission", sa.Integer(), nullable=False),
        sa.Column("protection_price", sa.Integer(), nullable=True),
        sa.Column("with_protection", sa.Boolean(), nullable=False),
        sa.Column("status", booking_status, server_default="pending_payment", nullable=False),
        sa.Column("reserved_until", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_bookings_event_id", "bookings", ["event_id"])
    op.create_index("ix_bookings_user_id", "bookings", ["user_id"])
    op.create_index("ix_bookings_status", "bookings", ["status"])
    op.create_index("ix_bookings_reserved_until", "bookings", ["reserved_until"])

    op.create_table(
        "event_seats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id"), nullable=False),
        sa.Column("seat_id", sa.Integer(), sa.ForeignKey("seats.id"), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("status", seat_status, server_default="available", nullable=False),
        sa.Column("reserved_until", sa.DateTime(), nullable=True),
        sa.Column("booking_id", sa.Integer(), sa.ForeignKey("bookings.id"), nullable=True),
        sa.UniqueConstraint("event_id", "seat_id", name="uq_event_seat"),
    )
    op.create_index("ix_event_seats_event_id", "event_seats", ["event_id"])
    op.create_index("ix_event_seats_seat_id", "event_seats", ["seat_id"])
    op.create_index("ix_event_seats_status", "event_seats", ["status"])
    op.create_index("ix_event_seats_booking_id", "event_seats", ["booking_id"])


def downgrade() -> None:
    op.drop_table("event_seats")
    op.drop_table("bookings")
    op.drop_table("events")
    op.drop_table("seats")
    op.drop_table("locations")
    postgresql.ENUM(name="booking_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="seat_status").drop(op.get_bind(), checkfirst=True)

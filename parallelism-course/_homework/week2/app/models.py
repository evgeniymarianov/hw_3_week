import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SeatStatus(str, enum.Enum):
    available = "available"
    reserved = "reserved"
    sold = "sold"


class BookingStatus(str, enum.Enum):
    pending_payment = "pending_payment"
    paid = "paid"
    cancelled = "cancelled"
    expired = "expired"


class Location(Base):
    """Площадка, где проходят мероприятия (например, Лужники, ВТБ-Арена)."""

    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    city: Mapped[str]
    address: Mapped[str]


class Seat(Base):
    """Место на площадке."""

    __tablename__ = "seats"
    __table_args__ = (
        UniqueConstraint("location_id", "sector", "row", "number", name="uq_seat_position"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), index=True)
    sector: Mapped[str] = mapped_column(index=True)
    row: Mapped[int]
    number: Mapped[int]
    x: Mapped[int]
    y: Mapped[int]


class Event(Base):
    """Мероприятие с датой, площадкой и базовой ценой. Создается организатором.
        Например: Концерт Аллы Пугачевой, Мастер-класс по Python."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    organizer_id: Mapped[int] = mapped_column(index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), index=True)
    title: Mapped[str]
    description: Mapped[str | None]
    category: Mapped[str]
    starts_at: Mapped[datetime] = mapped_column(DateTime(), index=True)
    base_price: Mapped[int]


class EventView(Base):
    """Количество просмотров мероприятия."""

    __tablename__ = "event_views"

    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), primary_key=True)
    views_count: Mapped[int] = mapped_column(default=0, server_default="0")


class Booking(Base):
    """Бронь пользователя на выбранные места."""

    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), index=True)
    user_id: Mapped[int] = mapped_column(index=True)
    amount: Mapped[int]  # суммарная стоимость всех выбранных мест
    payment_commission: Mapped[int]
    protection_price: Mapped[int | None]
    with_protection: Mapped[bool]
    status: Mapped[BookingStatus] = mapped_column(
        SAEnum(BookingStatus, name="booking_status"),
        default=BookingStatus.pending_payment,
        server_default=BookingStatus.pending_payment.value,
        index=True,
    )
    reserved_until: Mapped[datetime] = mapped_column(DateTime(), index=True)


class EventSeat(Base):
    """Место конкретного мероприятия с ценой и статусом."""

    __tablename__ = "event_seats"
    __table_args__ = (
        UniqueConstraint("event_id", "seat_id", name="uq_event_seat"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), index=True)
    seat_id: Mapped[int] = mapped_column(ForeignKey("seats.id"), index=True)
    price: Mapped[int]
    status: Mapped[SeatStatus] = mapped_column(
        SAEnum(SeatStatus, name="seat_status"),
        default=SeatStatus.available,
        server_default=SeatStatus.available.value,
        index=True,
    )
    reserved_until: Mapped[datetime | None] = mapped_column(DateTime())
    booking_id: Mapped[int | None] = mapped_column(
        ForeignKey("bookings.id"),
        index=True,
    )

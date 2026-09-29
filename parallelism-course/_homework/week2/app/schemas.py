from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models import BookingStatus, SeatStatus


class LocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    city: str
    address: str


class SeatRead(BaseModel):
    id: int
    location_id: int
    sector: str
    row: int
    number: int
    x: int
    y: int


class LocationDetail(BaseModel):
    location: LocationRead
    seats: list[SeatRead]


class EventCreate(BaseModel):
    location_id: int
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    category: str = Field(min_length=1, max_length=100)
    starts_at: datetime
    base_price: int = Field(gt=0)


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    organizer_id: int
    location_id: int
    title: str
    description: str | None
    category: str
    starts_at: datetime
    base_price: int


class EventSeatRead(BaseModel):
    id: int
    event_id: int
    seat_id: int
    sector: str
    row: int
    number: int
    x: int
    y: int
    price: int
    status: SeatStatus
    reserved_until: datetime | None
    booking_id: int | None


class BookingCreate(BaseModel):
    seat_ids: list[int] = Field(min_length=1)


class SalesDashboard(BaseModel):
    paid_orders: int
    sold_tickets: int
    revenue: int
    average_order: int


class OccupancyDashboard(BaseModel):
    total: int
    available: int
    reserved: int
    sold: int
    occupancy_percent: float


class EventDashboard(BaseModel):
    event_title: str
    starts_at: datetime
    sales: SalesDashboard
    occupancy: OccupancyDashboard


class PaymentQuote(BaseModel):
    commission: int
    total: int
    payment_methods: list[str]
    expires_at: datetime | None = None


class ProtectionQuote(BaseModel):
    available: bool
    price: int
    covered_amount: int
    description: str | None = None


class CheckoutBooking(BaseModel):
    id: int
    event_title: str
    starts_at: datetime
    seats: list[dict[str, Any]]
    base_amount: int
    payment_commission: int
    protection_price: int | None
    with_protection: bool
    reserved_until: datetime


class CheckoutResponse(BaseModel):
    booking: CheckoutBooking
    payment: PaymentQuote
    protection: ProtectionQuote | None


class PaymentCreate(BaseModel):
    payment_method: str
    with_protection: bool = False


class PaymentCompleted(BaseModel):
    booking_id: int
    status: BookingStatus
    charged_amount: int
    transaction_id: str

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, field_validator

from delivery_analytics.domain.enums import DeliveryStatus


class TrackingLocation(BaseModel):
    lat: float
    lon: float


class TrackingDestination(BaseModel):
    address: str | None = None
    lat: float | None = None
    lon: float | None = None


class DeliveryTrackingEvent(BaseModel):
    event_id: str
    event_type: str
    order_id: str
    courier_id: str
    darkstore_id: str
    status: DeliveryStatus
    courier_location: TrackingLocation | None = None
    destination: TrackingDestination
    recorded_at: datetime

    model_config = ConfigDict(use_enum_values=True)

    @field_validator("order_id", mode="before")
    @classmethod
    def normalize_order_id(cls, value: str | int) -> str:
        return str(value)

    @field_validator("recorded_at")
    @classmethod
    def normalize_recorded_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value

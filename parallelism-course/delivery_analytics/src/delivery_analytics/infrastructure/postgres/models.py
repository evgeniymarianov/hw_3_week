from datetime import datetime

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class CourierTrackingPointModel(Base):
    __tablename__ = "courier_tracking_points"

    courier_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
    )
    order_id: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(64), index=True)
    darkstore_id: Mapped[str] = mapped_column(String(128), index=True)
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)

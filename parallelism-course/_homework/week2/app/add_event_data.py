from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import engine
from app.models import Event, EventSeat, Location, Seat


async def add_event_data_to_db() -> None:
    async with AsyncSession(engine, expire_on_commit=False) as db:
        async with db.begin():
            if await db.scalar(select(func.count(Location.id))):
                print("Тестовые данные уже существуют")
                return

            location = Location(
                name="Центральный зал",
                city="Москва",
                address="Тверская улица, 1",
            )
            db.add(location)
            await db.flush()

            seats = []
            for row in range(1, 6):
                for number in range(1, 11):
                    seats.append(
                        Seat(
                            location_id=location.id,
                            sector="Основной сектор",
                            row=row,
                            number=number,
                            x=number * 50,
                            y=row * 50,
                        )
                    )
            db.add_all(seats)
            await db.flush()

            event = Event(
                organizer_id=1,
                location_id=location.id,
                title="Python Конференция",
                description="Тестовое мероприятие для домашнего задания",
                category="конференция",
                starts_at=datetime.now() + timedelta(days=30),
                base_price=5000,
            )
            db.add(event)
            await db.flush()

            db.add_all(
                EventSeat(event_id=event.id, seat_id=seat.id, price=event.base_price)
                for seat in seats
            )

    print("Тестовые данные созданы")


if __name__ == "__main__":
    import asyncio

    asyncio.run(add_event_data_to_db())

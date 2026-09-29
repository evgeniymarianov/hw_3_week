import asyncio
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from enum import StrEnum
import json
import os
import random
from typing import Annotated
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException, status
from faststream.kafka import KafkaBroker
from pydantic import BaseModel


API_KEY = "dl-L4pZ9cV2mH8qT6rN3xW7"
SPB_CENTER_LAT = 59.9386
SPB_CENTER_LON = 30.3141
DELIVERIES_DB_PATH = "deliveries.json"
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
STATUS_TOPIC = "delivery.status_events"
LOCATIONS_TOPIC = "courier.locations"
GPS_INTERVAL_SECONDS = 2
MIN_DELAY_SECONDS = 0.03
MAX_DELAY_SECONDS = 0.07

kafka_broker: KafkaBroker | None = None
lifecycle_tasks: set[asyncio.Task] = set()


class DeliveryStatus(StrEnum):
    COURIER_SEARCHING = "courier_searching"
    COURIER_FOUND = "courier_found"
    COURIER_ARRIVED_TO_DARKSTORE = "courier_arrived_to_darkstore"
    DELIVERING = "delivering"
    COMPLETED = "completed"


class DeliveryPriceRequest(BaseModel):
    address: str
    lat: float
    lon: float


class DeliveryCreateRequest(DeliveryPriceRequest):
    order_id: int
    darkstore_id: str = "darkstore_default"


async def _simulate_latency() -> None:
    await asyncio.sleep(random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS))


def _check_api_key(
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> None:
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Некорректный API-ключ",
        )


def _calculate_delivery_price(lat: float, lon: float) -> int:
    distance_factor = int(
        abs(lat - SPB_CENTER_LAT) * 100
        + abs(lon - SPB_CENTER_LON) * 100
    )
    return 199 + distance_factor


def _read_deliveries_db() -> dict[str, dict]:
    with open(DELIVERIES_DB_PATH) as file:
        return json.load(file)


def _write_deliveries_db(data: dict[str, dict]) -> None:
    with open(DELIVERIES_DB_PATH, "w") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )


def _create_delivery(order_id: int, darkstore_id: str) -> dict[str, str | int]:
    db = _read_deliveries_db()
    created_at = datetime.now(UTC)
    courier_found_at = created_at + timedelta(seconds=random.uniform(3, 30))
    courier_arrived_to_darkstore_at = courier_found_at + timedelta(seconds=20)
    delivering_at = courier_arrived_to_darkstore_at + timedelta(seconds=20)
    completed_at = delivering_at + timedelta(seconds=60)
    delivery_id = f"del-{uuid4().hex[:12]}"
    courier_id = f"courier_{random.randint(1, 20)}"
    estimated_delivery_at = created_at + timedelta(minutes=45)
    delivery = {
        "delivery_id": delivery_id,
        "order_id": order_id,
        "darkstore_id": darkstore_id,
        "courier_id": courier_id,
        "status": DeliveryStatus.COURIER_SEARCHING,
        "created_at": created_at.isoformat(),
        "courier_found_at": courier_found_at.isoformat(),
        "courier_arrived_to_darkstore_at": courier_arrived_to_darkstore_at.isoformat(),
        "delivering_at": delivering_at.isoformat(),
        "completed_at": completed_at.isoformat(),
        "estimated_delivery_at": estimated_delivery_at.isoformat(),
        "emitted_events": [],
    }
    db["deliveries"][delivery_id] = delivery
    _write_deliveries_db(db)

    return delivery


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _iso_z(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


async def _send_kafka_event(topic: str, key: str, payload: dict) -> None:
    if kafka_broker is None:
        return
    await kafka_broker.publish(payload, topic, key=key.encode())


async def _publish_status_event(
    delivery: dict,
    event_type: str,
    status_value: str,
    occurred_at: datetime,
) -> None:
    payload = {
        "event_id": f"{delivery['delivery_id']}:{event_type}",
        "event_type": event_type,
        "delivery_id": delivery["delivery_id"],
        "order_id": str(delivery["order_id"]),
        "courier_id": (
            None
            if event_type == "delivery_created"
            else delivery["courier_id"]
        ),
        "darkstore_id": delivery["darkstore_id"],
        "status": status_value,
        "occurred_at": _iso_z(occurred_at),
    }
    await _send_kafka_event(STATUS_TOPIC, delivery["delivery_id"], payload)


async def _publish_location_event(delivery: dict) -> None:
    now = datetime.now(UTC)
    seconds_from_start = max(
        0,
        int((now - _parse_datetime(delivery["courier_found_at"])).total_seconds()),
    )
    lat = SPB_CENTER_LAT + 0.001 * (seconds_from_start / 10) + random.uniform(-0.0005, 0.0005)
    lon = SPB_CENTER_LON + 0.001 * (seconds_from_start / 12) + random.uniform(-0.0005, 0.0005)
    payload = {
        "event_id": f"loc_{uuid4().hex}",
        "courier_id": delivery["courier_id"],
        "delivery_id": delivery["delivery_id"],
        "lat": round(lat, 6),
        "lon": round(lon, 6),
        "recorded_at": _iso_z(now),
    }
    await _send_kafka_event(LOCATIONS_TOPIC, delivery["courier_id"], payload)


def _status_events_schedule(delivery: dict) -> list[tuple[str, str, datetime]]:
    return [
        (
            "delivery_created",
            "created",
            _parse_datetime(delivery["created_at"]),
        ),
        (
            "courier_assigned",
            "courier_assigned",
            _parse_datetime(delivery["courier_found_at"]),
        ),
        (
            "order_picked_up",
            "picked_up",
            _parse_datetime(delivery["delivering_at"]),
        ),
        (
            "delivery_completed",
            "completed",
            _parse_datetime(delivery["completed_at"]),
        ),
    ]


async def _run_delivery_lifecycle(delivery_id: str) -> None:
    while True:
        db = _read_deliveries_db()
        delivery = db["deliveries"].get(delivery_id)
        if delivery is None:
            return

        now = datetime.now(UTC)
        emitted_events = set(delivery.get("emitted_events", []))
        changed = False
        for event_type, status_value, occurred_at in _status_events_schedule(delivery):
            if event_type in emitted_events or now < occurred_at:
                continue
            await _publish_status_event(delivery, event_type, status_value, occurred_at)
            emitted_events.add(event_type)
            delivery["status"] = status_value
            changed = True

        delivery["emitted_events"] = sorted(emitted_events)
        if changed:
            db["deliveries"][delivery_id] = delivery
            _write_deliveries_db(db)

        if (
            now >= _parse_datetime(delivery["courier_found_at"])
            and now < _parse_datetime(delivery["completed_at"])
        ):
            await _publish_location_event(delivery)

        if "delivery_completed" in emitted_events:
            return

        await asyncio.sleep(GPS_INTERVAL_SECONDS)


def _start_lifecycle_task(delivery_id: str) -> None:
    task = asyncio.create_task(_run_delivery_lifecycle(delivery_id))
    lifecycle_tasks.add(task)
    task.add_done_callback(lifecycle_tasks.discard)


@asynccontextmanager
async def lifespan(_: FastAPI):
    global kafka_broker
    kafka_broker = KafkaBroker(KAFKA_BOOTSTRAP_SERVERS)
    await kafka_broker.start()
    for delivery_id, delivery in _read_deliveries_db()["deliveries"].items():
        if "delivery_completed" not in set(delivery.get("emitted_events", [])):
            _start_lifecycle_task(delivery_id)
    try:
        yield
    finally:
        for task in lifecycle_tasks:
            task.cancel()
        await asyncio.gather(*lifecycle_tasks, return_exceptions=True)
        if kafka_broker is not None:
            await kafka_broker.stop()


app = FastAPI(title="API Доставки", lifespan=lifespan)


@app.post("/deliveries/price")
async def get_delivery_price(
    data: DeliveryPriceRequest,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> dict[str, int]:
    _check_api_key(x_api_key)
    await _simulate_latency()

    return {"price": _calculate_delivery_price(data.lat, data.lon)}


@app.post("/deliveries")
async def create_delivery(
    data: DeliveryCreateRequest,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> dict[str, str | int]:
    _check_api_key(x_api_key)
    await _simulate_latency()

    delivery = _create_delivery(
        order_id=data.order_id,
        darkstore_id=data.darkstore_id,
    )
    _start_lifecycle_task(delivery["delivery_id"])

    return {
        "delivery_id": delivery["delivery_id"],
        "order_id": data.order_id,
        "status": delivery["status"],
    }


@app.get("/deliveries/{delivery_id}")
async def get_delivery_info(
    delivery_id: str,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> dict[str, str | int | list[str]]:
    _check_api_key(x_api_key)
    await _simulate_latency()

    db = _read_deliveries_db()
    delivery = db["deliveries"].get(delivery_id)

    if delivery is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Доставка не найдена",
        )

    now = datetime.now(UTC)

    if now >= datetime.fromisoformat(delivery["completed_at"]):
        delivery["status"] = DeliveryStatus.COMPLETED
    elif now >= datetime.fromisoformat(delivery["delivering_at"]):
        delivery["status"] = DeliveryStatus.DELIVERING
    elif now >= datetime.fromisoformat(delivery["courier_arrived_to_darkstore_at"]):
        delivery["status"] = DeliveryStatus.COURIER_ARRIVED_TO_DARKSTORE
    elif now >= datetime.fromisoformat(delivery["courier_found_at"]):
        delivery["status"] = DeliveryStatus.COURIER_FOUND
    else:
        delivery["status"] = DeliveryStatus.COURIER_SEARCHING

    db["deliveries"][delivery_id] = delivery
    _write_deliveries_db(db)

    return delivery

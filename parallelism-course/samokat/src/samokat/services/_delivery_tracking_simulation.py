import asyncio
import math
import random
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from faststream.kafka import KafkaBroker, KafkaPublishMessage

from samokat.config import KafkaConfig

SIMULATION_ROUTES = (
    {
        "name": "Невский проспект",
        "darkstore_id": "darkstore_central",
        "points": (
            (59.936676, 30.315806),
            (59.935822, 30.323922),
            (59.934821, 30.333821),
            (59.933716, 30.342012),
            (59.932684, 30.349432),
        ),
    },
    {
        "name": "Лиговский проспект",
        "darkstore_id": "darkstore_central",
        "points": (
            (59.936474, 30.355135),
            (59.930684, 30.356044),
            (59.925105, 30.356012),
            (59.920632, 30.355422),
            (59.915842, 30.354832),
        ),
    },
    {
        "name": "Московский проспект",
        "darkstore_id": "darkstore_south",
        "points": (
            (59.916011, 30.318421),
            (59.908624, 30.319033),
            (59.899315, 30.319424),
            (59.890782, 30.319848),
            (59.883318, 30.320118),
        ),
    },
    {
        "name": "Каменностровский проспект",
        "darkstore_id": "darkstore_north",
        "points": (
            (59.965792, 30.310352),
            (59.970614, 30.307428),
            (59.976216, 30.303552),
            (59.982118, 30.299422),
            (59.986612, 30.296322),
        ),
    },
    {
        "name": "Средний проспект Васильевского острова",
        "darkstore_id": "darkstore_west",
        "points": (
            (59.942127, 30.276157),
            (59.943012, 30.263241),
            (59.943904, 30.250418),
            (59.944938, 30.238220),
            (59.945953, 30.226381),
        ),
    },
)

SIMULATION_CENTER = (59.9386, 30.3141)
SIMULATION_AREA_NORTH_RADIUS_METERS = 3_100.0
SIMULATION_AREA_EAST_RADIUS_METERS = 4_300.0
COURIER_CENTER_MIN_DISTANCE_METERS = 380.0
COURIER_CENTER_MAX_ATTEMPTS_MULTIPLIER = 1_000
COURIER_ROUTE_FORWARD_METERS = 58.0
COURIER_ROUTE_LATERAL_METERS = 34.0


class DeliveryTrackingSimulationService:
    def __init__(self, broker: KafkaBroker, config: KafkaConfig) -> None:
        self._publish_concurrency = 100
        self._broker = broker
        self._config = config

    async def run_simulation(
        self,
        couriers_count: int = 100,
        events_count: int = 20_000,  # настройка количества событий
        duration_seconds: float = 10.0,
    ) -> None:
        couriers = self._build_couriers(couriers_count)
        tick_targets = self._build_tick_targets(events_count)
        started_monotonic = asyncio.get_running_loop().time()
        started_at = datetime.now(UTC)

        for tick_index, tick_events_count in enumerate(tick_targets):
            event_time = started_at + timedelta(
                seconds=duration_seconds * tick_index / len(tick_targets),
            )
            payloads = [
                self._build_event(self._choose_courier(couriers), event_time)
                for _ in range(tick_events_count)
            ]
            await self._publish_payloads(payloads)

            next_tick = started_monotonic + (
                duration_seconds * (tick_index + 1) / len(tick_targets)
            )
            sleep_seconds = next_tick - asyncio.get_running_loop().time()
            if sleep_seconds > 0:
                await asyncio.sleep(sleep_seconds)

    async def _publish_payloads(self, payloads: list[dict]) -> None:
        for start in range(0, len(payloads), self._publish_concurrency):
            chunk = payloads[start: start + self._publish_concurrency]

            # for event in chunk:
            #     await self._broker.publish(
            #         message=event,
            #         topic=self._config.tracking_topic,
            #         key=event["courier_id"].encode(),
            #     )

            await self._broker.publish_batch(
                *[
                    KafkaPublishMessage(
                        body=event,
                        key=event["courier_id"].encode(),
                    )
                    for event in chunk
                ],
                topic=self._config.tracking_topic,
            )

    def _build_couriers(self, couriers_count: int = 100) -> list[dict]:
        couriers = []
        centers = self._build_courier_centers(couriers_count)
        routes_count = len(SIMULATION_ROUTES)
        for index in range(couriers_count):
            route_index = index % routes_count
            route = SIMULATION_ROUTES[route_index]
            route_points = self._build_personal_route_points(centers[index])
            rate_weight = self._rate_weight(index)
            speed_mps = random.uniform(3.5, 6.5)
            couriers.append(
                {
                    "courier_id": f"courier_{index + 1}",
                    "delivery_id": f"del-sim-{100_000 + index + 1}",
                    "order_id": 100_000 + index + 1,
                    "route": route,
                    "route_points": route_points,
                    "route_point_index": 0,
                    "direction": 1,
                    "lat": route_points[0][0],
                    "lon": route_points[0][1],
                    "last_recorded_at": None,
                    "rate_weight": rate_weight,
                    "speed_mps": speed_mps,
                },
            )
        return couriers

    def _build_courier_centers(
        self,
        couriers_count: int,
    ) -> list[tuple[float, float]]:
        centers: list[tuple[float, float]] = []
        attempts_limit = couriers_count * COURIER_CENTER_MAX_ATTEMPTS_MULTIPLIER

        for _ in range(attempts_limit):
            if len(centers) >= couriers_count:
                return centers

            radius = math.sqrt(random.random())
            angle = random.uniform(0, 2 * math.pi)
            north_offset = (
                math.sin(angle) * radius * SIMULATION_AREA_NORTH_RADIUS_METERS
            )
            east_offset = math.cos(angle) * radius * SIMULATION_AREA_EAST_RADIUS_METERS
            center = self._offset_point(
                SIMULATION_CENTER[0],
                SIMULATION_CENTER[1],
                north_offset,
                east_offset,
            )

            if all(
                self._distance_meters(center[0], center[1], lat, lon)
                >= COURIER_CENTER_MIN_DISTANCE_METERS
                for lat, lon in centers
            ):
                centers.append(center)

        msg = f"Could not place {couriers_count} couriers without overlapping routes"
        raise RuntimeError(msg)

    def _build_personal_route_points(
        self,
        center: tuple[float, float],
    ) -> tuple[tuple[float, float], ...]:
        heading = random.uniform(0, 2 * math.pi)
        forward = COURIER_ROUTE_FORWARD_METERS
        lateral = COURIER_ROUTE_LATERAL_METERS
        local_points = (
            (-forward, random.uniform(-0.35, 0.35) * lateral),
            (-0.45 * forward, random.uniform(-1.0, 1.0) * lateral),
            (0.05 * forward, random.uniform(-0.85, 0.85) * lateral),
            (0.55 * forward, random.uniform(-1.0, 1.0) * lateral),
            (forward, random.uniform(-0.35, 0.35) * lateral),
        )
        return tuple(
            self._build_route_point(center, heading, forward_offset, lateral_offset)
            for forward_offset, lateral_offset in local_points
        )

    def _build_route_point(
        self,
        center: tuple[float, float],
        heading: float,
        forward_offset_meters: float,
        lateral_offset_meters: float,
    ) -> tuple[float, float]:
        north_offset, east_offset = self._rotate_offset(
            forward_offset_meters,
            lateral_offset_meters,
            heading,
        )
        return self._offset_point(center[0], center[1], north_offset, east_offset)

    def _rotate_offset(
        self,
        north_offset_meters: float,
        east_offset_meters: float,
        angle_radians: float,
    ) -> tuple[float, float]:
        cos_angle = math.cos(angle_radians)
        sin_angle = math.sin(angle_radians)
        return (
            north_offset_meters * cos_angle - east_offset_meters * sin_angle,
            north_offset_meters * sin_angle + east_offset_meters * cos_angle,
        )

    def _offset_point(
        self,
        lat: float,
        lon: float,
        north_offset_meters: float,
        east_offset_meters: float,
    ) -> tuple[float, float]:
        offset_lat = lat + north_offset_meters / 111_320
        offset_lon = lon + east_offset_meters / (
            111_320 * math.cos(math.radians(offset_lat))
        )
        return offset_lat, offset_lon

    def _rate_weight(self, index: int) -> float:
        if index < 55:
            return random.uniform(1, 3)
        if index < 88:
            return random.uniform(8, 18)
        return random.uniform(45, 80)

    def _build_tick_targets(self, events_count: int) -> list[int]:
        second_targets = [800, 1200, 1900, 2600, 3800, 4600, 2300, 1500, 900, 400]
        scale = events_count / sum(second_targets)
        targets = []
        remaining = events_count

        for second_index, second_target in enumerate(second_targets):
            target = int(round(second_target * scale))
            if second_index == len(second_targets) - 1:
                target = remaining
            remaining -= target

            tick_weights = [random.uniform(0.4, 1.4) for _ in range(10)]
            tick_weights[random.randrange(10)] *= random.uniform(3.0, 6.0)
            weight_sum = sum(tick_weights)
            tick_targets = [
                int(target * weight / weight_sum) for weight in tick_weights
            ]
            tick_targets[-1] += target - sum(tick_targets)
            targets.extend(tick_targets)

        return targets

    def _choose_courier(self, couriers: list[dict]) -> dict:
        return random.choices(
            couriers,
            weights=[courier["rate_weight"] for courier in couriers],
            k=1,
        )[0]

    def _build_event(self, courier: dict, recorded_at: datetime) -> dict:
        self._advance_courier(courier, recorded_at)
        route = courier["route"]
        points = self._ordered_points(courier)
        destination = points[-1]

        return {
            "event_id": f"{courier['delivery_id']}:{uuid4().hex}",
            "event_type": "courier_location_updated",
            "delivery_id": courier["delivery_id"],
            "order_id": courier["order_id"],
            "courier_id": courier["courier_id"],
            "darkstore_id": route["darkstore_id"],
            "status": "delivering",
            "courier_location": {
                "lat": round(courier["lat"], 6),
                "lon": round(courier["lon"], 6),
            },
            "destination": {
                "address": f"{route['name']}, маршрут {courier['courier_id']}",
                "lat": destination[0],
                "lon": destination[1],
            },
            "recorded_at": recorded_at.isoformat().replace("+00:00", "Z"),
        }

    def _advance_courier(self, courier: dict, recorded_at: datetime) -> None:
        previous_recorded_at = courier["last_recorded_at"] or recorded_at
        delta_seconds = max(0.0, (recorded_at - previous_recorded_at).total_seconds())
        courier["last_recorded_at"] = recorded_at
        step_meters = min(10.0, max(0.2, courier["speed_mps"] * delta_seconds))
        self._advance_on_route(courier, step_meters)

    def _ordered_points(self, courier: dict) -> tuple[tuple[float, float], ...]:
        points = courier["route_points"]
        if courier["direction"] == 1:
            return points
        return tuple(reversed(points))

    def _advance_on_route(self, courier: dict, step_meters: float) -> None:
        points = self._ordered_points(courier)
        segment_index = courier["route_point_index"]

        while step_meters > 0:
            if segment_index >= len(points) - 1:
                courier["direction"] *= -1
                courier["route_point_index"] = 0
                points = self._ordered_points(courier)
                segment_index = 0

            target_lat, target_lon = points[segment_index + 1]
            distance = self._distance_meters(
                courier["lat"],
                courier["lon"],
                target_lat,
                target_lon,
            )
            if distance <= step_meters:
                courier["lat"] = target_lat
                courier["lon"] = target_lon
                segment_index += 1
                courier["route_point_index"] = segment_index
                step_meters -= distance
                continue

            ratio = step_meters / distance
            courier["lat"] += (target_lat - courier["lat"]) * ratio
            courier["lon"] += (target_lon - courier["lon"]) * ratio
            break

    def _distance_meters(
        self,
        lat_from: float,
        lon_from: float,
        lat_to: float,
        lon_to: float,
    ) -> float:
        average_lat = math.radians((lat_from + lat_to) / 2)
        lat_meters = (lat_to - lat_from) * 111_320
        lon_meters = (lon_to - lon_from) * 111_320 * math.cos(average_lat)
        return math.hypot(lat_meters, lon_meters)

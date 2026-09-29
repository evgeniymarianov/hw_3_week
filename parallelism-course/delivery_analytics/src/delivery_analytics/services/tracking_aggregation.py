import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from delivery_analytics.infrastructure.postgres.manager import DatabaseManager
from delivery_analytics.services.websocket_gps_broadcaster import WebsocketGPSBroadcaster

logger = logging.getLogger(__name__)

COURIER_TRACKING_MIN_INTERVAL = timedelta(milliseconds=500)


class TrackingAggregationService:
    def __init__(
        self,
        db: DatabaseManager,
        ws_broadcaster: WebsocketGPSBroadcaster,
    ) -> None:
        self.db = db
        self.ws_broadcaster = ws_broadcaster

    async def process(self, events: list[Any]) -> None:
        tracking_points = self._prepare_tracking_points(events)
        if not tracking_points:
            return

        await self._store_tracking_points(tracking_points)
        _ = asyncio.create_task(
            self.ws_broadcaster.broadcast_courier_tracking_events(tracking_points),
        )

    def _prepare_tracking_points(
        self,
        events: list[Any],
    ) -> list[dict[str, Any]]:
        return self._drop_intermediate_points(
            self._deduplicate_tracking_points(
                [self._build_tracking_point(event) for event in events],
            ),
        )

    def _deduplicate_tracking_points(
        self,
        tracking_points: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        tracking_points_by_key: dict[tuple[str, datetime], dict[str, Any]] = {}
        for tracking_point in tracking_points:
            tracking_points_by_key[
                (
                    tracking_point["courier_id"],
                    tracking_point["recorded_at"],
                )
            ] = tracking_point

        return list(tracking_points_by_key.values())

    def _drop_intermediate_points(
        self,
        tracking_points: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        tracking_points_by_courier: dict[str, list[dict[str, Any]]] = {}
        for tracking_point in tracking_points:
            tracking_points_by_courier.setdefault(
                tracking_point["courier_id"],
                [],
            ).append(tracking_point)

        kept_keys = set()
        for courier_tracking_points in tracking_points_by_courier.values():
            last_recorded_at = None
            for tracking_point in sorted(
                courier_tracking_points,
                key=lambda item: item["recorded_at"],
            ):
                recorded_at = tracking_point["recorded_at"]
                if (
                    last_recorded_at is not None
                    and recorded_at - last_recorded_at < COURIER_TRACKING_MIN_INTERVAL
                ):
                    continue

                kept_keys.add(
                    (
                        tracking_point["courier_id"],
                        tracking_point["recorded_at"],
                    ),
                )
                last_recorded_at = recorded_at

        return [
            tracking_point
            for tracking_point in tracking_points
            if (
                tracking_point["courier_id"],
                tracking_point["recorded_at"],
            )
            in kept_keys
        ]

    async def _store_tracking_points(
        self, tracking_points: list[dict[str, Any]]
    ) -> None:
        await self.db.tracking_points.upsert_many(tracking_points)
        await self.db.commit()

    def _build_tracking_point(
        self,
        event: Any,
    ) -> dict[str, Any]:
        return {
            "courier_id": event.courier_id,
            "order_id": event.order_id,
            "status": event.status,
            "darkstore_id": event.darkstore_id,
            "lat": event.courier_location.lat,
            "lon": event.courier_location.lon,
            "recorded_at": event.recorded_at,
        }

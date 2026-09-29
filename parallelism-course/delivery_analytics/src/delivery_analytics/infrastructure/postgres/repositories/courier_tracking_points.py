from collections.abc import Sequence
from typing import Any

from sqlalchemy.dialects.postgresql import insert as pg_insert

from delivery_analytics.infrastructure.postgres.models import (
    CourierTrackingPointModel,
)
from delivery_analytics.infrastructure.postgres.repositories.base import BaseRepo


class CourierTrackingPointRepository(BaseRepo):
    async def upsert_many(self, rows: Sequence[dict[str, Any]]) -> None:
        if not rows:
            return

        stmt = pg_insert(CourierTrackingPointModel).values(list(rows))
        excluded = stmt.excluded
        await self.session.execute(
            stmt.on_conflict_do_update(
                index_elements=["courier_id", "recorded_at"],
                set_={
                    "order_id": excluded.order_id,
                    "status": excluded.status,
                    "darkstore_id": excluded.darkstore_id,
                    "lat": excluded.lat,
                    "lon": excluded.lon,
                },
            ),
        )

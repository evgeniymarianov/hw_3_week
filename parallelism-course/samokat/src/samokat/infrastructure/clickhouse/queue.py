import asyncio
from datetime import datetime, UTC

from samokat.infrastructure.clickhouse.manager import ClickHouseManager
from samokat.infrastructure.clickhouse.schemas import UserEvent


class ClickhouseEventQueue:
    def __init__(self, clickhouse_client: ClickHouseManager):
        self._queue = asyncio.Queue()
        self.ch = clickhouse_client

    def start(self):
        self._worker_task = asyncio.create_task(self._flush_events())

    async def stop(self):
        self._worker_task.cancel()

        try:
            await self._worker_task
        except:
            pass

    def add_user_event(
        self,
        user_id: int,
        event: str,
        category: str,
    ):
        # print("ADD EVENT")
        self._queue.put_nowait(UserEvent(
            user_id=user_id,
            event=event,
            category=category,
            event_time=datetime.now(UTC),
        ))

    async def _flush_events(self):
        events = []
        while True:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=5)
                events.append(event)
            except asyncio.TimeoutError:
                if len(events) > 0:
                    await self._insert_events_to_db(events)
                    events = []
                    continue

            if len(events) >= 10:
                await self._insert_events_to_db(events)
                events = []

    async def _insert_events_to_db(self, events: list[UserEvent]):
        # print(f"INSERTING {len(events)} EVENTS")
        await self.ch.insert_user_events(events)

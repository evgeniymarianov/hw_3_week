"""Агрегация просмотров мероприятий в памяти и батчевая запись в PostgreSQL.

Проблема: если популярное мероприятие откроют много раз за короткое время,
вставлять каждый просмотр отдельной строкой в event_views — лишняя нагрузка
на базу.

Решение (по образцу ClickhouseEventQueue из samokat):
  1. Уникальный (после Redis-дедупликации) просмотр кладётся в asyncio.Queue.
  2. Фоновый воркер читает события из очереди и агрегирует их в памяти по
     event_id: суммарное число просмотров, а не отдельные записи.
  3. Накопленное пишется в БД одним UPDATE-ом на мероприятие (+N к счётчику)
     каждые FLUSH_BATCH_SIZE событий либо раз в FLUSH_INTERVAL_SECONDS секунд.
  4. При остановке приложения воркер корректно завершается: очередь
     опустошается, оставшиеся агрегаты сбрасываются в базу (shutdown),
     чтобы не потерять просмотры.
"""

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db import engine
from app.models import EventView

logger = logging.getLogger(__name__)

FLUSH_BATCH_SIZE = 10  # писать в БД, когда накоплено N событий
FLUSH_INTERVAL_SECONDS = 5  # либо раз в 5 секунд


class ViewEventQueue:
    """Очередь просмотров + фоновый воркер-агрегатор."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[int] = asyncio.Queue()
        self._counters: dict[int, int] = {}  # накопленные в памяти агрегаты
        self._worker_task: asyncio.Task | None = None

    def start(self) -> None:
        """Запускает фонового воркера (вызывается из lifespan при старте)."""
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._flush_events())

    async def stop(self) -> None:
        """Останавливает воркера и дописывает оставшиеся агрегаты в БД."""
        if self._worker_task is not None:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None

        # Всё, что не успело записаться (черновик воркера + остатки очереди),
        # корректно сбрасываем в базу, чтобы не потерять просмотры.
        await self._flush()

    def add_view(self, event_id: int) -> None:
        """Кладёт уникальный просмотр в очередь (не блокируя обработчик запроса)."""
        self._queue.put_nowait(event_id)

    async def _flush_events(self) -> None:
        """Фоновый воркер: читает просмотры из очереди, агрегирует их в памяти
        и пишет в БД каждые FLUSH_BATCH_SIZE событий либо раз в FLUSH_INTERVAL_SECONDS.
        """
        while True:
            try:
                event_id = await asyncio.wait_for(
                    self._queue.get(), timeout=FLUSH_INTERVAL_SECONDS
                )
            except asyncio.TimeoutError:
                # Прошло 5 секунд — пишем то, что накопили
                await self._flush()
                continue

            # Агрегируем на уровне Python: суммарное число просмотров по мероприятию
            self._counters[event_id] = self._counters.get(event_id, 0) + 1

            if sum(self._counters.values()) >= FLUSH_BATCH_SIZE:
                # Накопили 10 событий — пишем в базу одним обновлением счётчика
                await self._flush()

    async def _flush(self) -> None:
        """Сбрасывает в БД всё накопленное: агрегаты воркера и остатки очереди."""
        while not self._queue.empty():
            try:
                event_id = self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            self._counters[event_id] = self._counters.get(event_id, 0) + 1

        counters, self._counters = self._counters, {}
        await self._write_counters(counters)

    async def _write_counters(self, counters: dict[int, int]) -> None:
        """Одно обновление счётчика на мероприятие: views_count += сумма просмотров."""
        if not counters:
            return
        logger.info("Flushing %d aggregated view events", sum(counters.values()))
        async with AsyncSession(engine, expire_on_commit=False) as db:
            async with db.begin():
                for event_id, views in counters.items():
                    # UPSERT: если строки счётчика ещё нет — создаём с нужным
                    # значением, если есть — атомарно инкрементим на +views.
                    stmt = pg_insert(EventView).values(
                        event_id=event_id, views_count=views
                    )
                    stmt = stmt.on_conflict_do_update(
                        index_elements=[EventView.event_id],
                        set_={
                            EventView.views_count.name: EventView.views_count + stmt.excluded.views_count
                        },
                    )
                    await db.execute(stmt)


view_event_queue = ViewEventQueue()

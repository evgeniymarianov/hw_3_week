"""Кэш мероприятий в Redis + распределённый SingleFlight через Redis Lock.

Проблема (cache stampede / thundering herd): если открылось популярное
мероприятие и кэш пуст, множество одновременных запросов провалятся в
PostgreSQL за одним и тем же событием.

Решение — распределённый SingleFlight:
  1. Проверяем Redis-кэш. Есть данные — возвращаем.
  2. Данных нет — пытаемся взять Redis Lock на загрузку этого мероприятия.
  3. Процесс, получивший lock, ЕЩЁ РАЗ проверяет кэш (пока мы ждали lock,
     данные мог положить другой процесс), при необходимости идёт в БД,
     кладёт результат в Redis и отпускает lock.
  4. Процессы, не получившие lock, коротко ждут его отпускания и повторно
     читают Redis; по таймауту падают с ошибкой 503.
"""

import asyncio
import logging

from redis.asyncio import Redis
from redis.exceptions import LockError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import engine
from app.models import Event
from app.redis_client import redis_client
from app.schemas import EventRead

logger = logging.getLogger(__name__)

EVENT_CACHE_TTL_SECONDS = 60
LOCK_TIMEOUT_SECONDS = 5  # авто-снятие lock, если владелец упал вместе с процессом
BLOCKING_TIMEOUT_SECONDS = 3  # сколько ждём чужой lock
POLL_INTERVAL_SECONDS = 0.05  # как часто перепроверяем кэш, пока ждём lock


class EventCacheMissTimeout(Exception):
    """Не дождались загрузки мероприятия другим процессом по таймауту."""


def _event_cache_key(event_id: int) -> str:
    return f"events:card:{event_id}"


def _event_lock_key(event_id: int) -> str:
    return f"locks:events:load:{event_id}"


async def get_event_from_cache(event_id: int, redis: Redis = redis_client) -> EventRead | None:
    """Читает мероприятие из Redis-кэша."""
    cached = await redis.get(_event_cache_key(event_id))
    if cached is None:
        return None
    return EventRead.model_validate_json(cached)


async def set_event_in_cache(
    event: EventRead,
    ttl: int = EVENT_CACHE_TTL_SECONDS,
    redis: Redis = redis_client,
) -> None:
    """Кладёт мероприятие в Redis-кэш."""
    await redis.set(_event_cache_key(event.id), event.model_dump_json(), ex=ttl)


async def load_event_from_db(event_id: int) -> EventRead | None:
    """Сходит в PostgreSQL за мероприятием."""
    async with AsyncSession(engine, expire_on_commit=False) as db:
        event = await db.scalar(select(Event).where(Event.id == event_id))
        if event is None:
            return None
        return EventRead.model_validate(event)


async def get_event_single_flight(
    event_id: int,
    redis: Redis = redis_client,
) -> EventRead:
    """Возвращает мероприятие, гарантируя что на cache miss в БД пойдёт только один запрос.

    :raises EventNotFoundError: мероприятия нет в БД.
    :raises EventCacheMissTimeout: не дождались результата загрузки по таймауту.
    """
    # 1. Быстрая проверка кэша
    event = await get_event_from_cache(event_id, redis)
    if event is not None:
        return event

    # 2. Cache miss — пробуем взять распределённый lock на загрузку этого события
    lock = redis.lock(
        _event_lock_key(event_id),
        timeout=LOCK_TIMEOUT_SECONDS,
        blocking_timeout=BLOCKING_TIMEOUT_SECONDS,
        thread_local=False,
    )

    if not await lock.acquire(blocking=False):
        # 3a. Lock уже у кого-то другого — коротко ждём, что он положит данные в кэш
        return await _wait_for_cached_event(event_id, redis)

    try:
        # 3b. Получили lock — ещё раз проверяем кэш (double-check):
        # пока мы брали lock, данные мог загрузить предыдущий владелец lock
        event = await get_event_from_cache(event_id, redis)
        if event is not None:
            return event

        # 4. Идём в PostgreSQL, сохраняем результат в Redis
        event = await load_event_from_db(event_id)
        if event is None:
            raise EventNotFoundError(event_id)

        await set_event_in_cache(event, redis=redis)
        return event
    finally:
        # 5. Отпускаем lock. LockError — если lock уже истёл по timeout
        try:
            await lock.release()
        except LockError:
            logger.warning("Lock for event %s already expired", event_id)


async def _wait_for_cached_event(event_id: int, redis: Redis) -> EventRead:
    """Опрашивает кэш, пока держатель lock загружает мероприятие."""
    deadline = BLOCKING_TIMEOUT_SECONDS
    waited = 0.0
    while waited < deadline:
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
        waited += POLL_INTERVAL_SECONDS

        event = await get_event_from_cache(event_id, redis)
        if event is not None:
            return event

    raise EventCacheMissTimeout(
        f"Timed out waiting for another process to load event {event_id}"
    )


class EventNotFoundError(Exception):
    def __init__(self, event_id: int) -> None:
        super().__init__(f"Event {event_id} not found")
        self.event_id = event_id

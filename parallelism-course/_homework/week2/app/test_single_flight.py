"""Интеграционный тест распределённого SingleFlight для GET /events/{event_id}.

Запускается на fakeredis (реального Redis не нужен). Проверяет:
  1. При N одновременных cache miss в БД за мероприятием идёт РОВНО 1 запрос,
     остальные забирают результат из Redis-кэша.
  2. Повторные запросы читаются из кэша, БД больше не трогается.
  3. Если держатель lock не успел положить данные — ожидающий падает по таймауту.
"""

import asyncio
import sys
import types

# Заглушка для app.db до импорта модулей приложения (реальный PostgreSQL не нужен)
db_stub = types.ModuleType("app.db")
db_stub.engine = None
sys.modules["app.db"] = db_stub

import fakeredis.aioredis  # noqa: E402

import event_cache  # noqa: E402
from schemas import EventRead  # noqa: E402

EVENT_ID = 1

db_calls = 0


def make_event() -> EventRead:
    from datetime import datetime

    return EventRead(
        id=EVENT_ID,
        organizer_id=1,
        location_id=1,
        title="Python Конференция",
        description="Тест",
        category="конференция",
        starts_at=datetime(2026, 10, 30),
        base_price=5000,
    )


async def fake_load_from_db(event_id: int) -> EventRead | None:
    """Имитируем медленный запрос к PostgreSQL."""
    global db_calls
    db_calls += 1
    await asyncio.sleep(0.2)
    return make_event()


async def main() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

    # Подменяем источник данных и Redis-клиент
    original_loader = event_cache.load_event_from_db
    event_cache.load_event_from_db = fake_load_from_db
    try:
        # --- 1. Шторм из 50 одновременных cache-miss запросов ---
        results = await asyncio.gather(
            *[event_cache.get_event_single_flight(EVENT_ID, redis=redis) for _ in range(50)]
        )
        assert all(r == make_event() for r in results), "все запросы должны вернуть одно событие"
        assert db_calls == 1, f"в БД должен быть ровно 1 запрос, было: {db_calls}"
        print(f"OK: 50 одновременных cache miss -> {db_calls} запрос в БД")

        # --- 2. Данные лежат в кэше, повторный запрос не трогает БД ---
        cached = await event_cache.get_event_from_cache(EVENT_ID, redis=redis)
        assert cached == make_event(), "событие должно быть в Redis"
        await event_cache.get_event_single_flight(EVENT_ID, redis=redis)
        assert db_calls == 1, "повторный запрос должен читаться из кэша"
        print("OK: повторные запросы читаются из Redis, БД не тронута")

        # --- 3. Lock занят, данные не появляются -> таймаут ---
        await redis.delete(event_cache._event_cache_key(EVENT_ID))
        holder_lock = redis.lock(
            event_cache._event_lock_key(EVENT_ID),
            timeout=event_cache.LOCK_TIMEOUT_SECONDS + 10,
        )
        await holder_lock.acquire()
        event_cache.BLOCKING_TIMEOUT_SECONDS = 0.3
        try:
            await event_cache.get_event_single_flight(EVENT_ID, redis=redis)
            raise AssertionError("ожидался EventCacheMissTimeout")
        except event_cache.EventCacheMissTimeout:
            print("OK: ожидание чужого lock завершилось таймаутом (EventCacheMissTimeout)")
        finally:
            await holder_lock.release()
            event_cache.BLOCKING_TIMEOUT_SECONDS = 3.0

        # --- 4. Мероприятия нет в БД -> 404 (EventNotFoundError) ---
        async def missing(_id: int):
            return None

        event_cache.load_event_from_db = missing
        await redis.delete(event_cache._event_cache_key(EVENT_ID))
        try:
            await event_cache.get_event_single_flight(999, redis=redis)
            raise AssertionError("ожидался EventNotFoundError")
        except event_cache.EventNotFoundError:
            print("OK: несуществующее мероприятие -> EventNotFoundError (404)")
 
        # --- 5. Lock освобождается после загрузки ---
        assert not await redis.exists(event_cache._event_lock_key(EVENT_ID)), \
            "lock должен быть отпущен"
        print("OK: lock отпущен после загрузки")
    finally:
        event_cache.load_event_from_db = original_loader

    print("\nВсе проверки SingleFlight пройдены")


if __name__ == "__main__":
    asyncio.run(main())

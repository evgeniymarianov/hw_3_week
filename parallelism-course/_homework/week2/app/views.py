"""Сервис учёта просмотров мероприятий.

Логика (по образцу CartService.add_item из samokat, который под капотом
использует очередь событий с _flush_events):

  1. Дедупликация через Redis: просмотр того же мероприятия с того же IP
     засчитывается не чаще одного раза за VIEW_DEDUPE_TTL_SECONDS (5 минут).
     Ключ ставится атомарно (SET NX EX), чтобы гонка параллельных запросов
     не привела к двойному учёту.
  2. Если просмотр уникальный — он отправляется в asyncio.Queue
     (ViewEventQueue), где фоновый воркер агрегирует его в памяти и пишет
     в PostgreSQL батчами (каждые 10 событий либо раз в 5 секунд).
"""

import logging

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.redis_client import redis_client
from app.view_queue import view_event_queue

logger = logging.getLogger(__name__)

VIEW_DEDUPE_TTL_SECONDS = 5 * 60  # один просмотр с одного IP — раз в 5 минут


def _view_dedupe_key(event_id: int, ip: str) -> str:
    return f"views:dedupe:{event_id}:{ip}"


class ViewService:
    def __init__(self, redis: Redis = redis_client) -> None:
        self.redis = redis

    async def register_view(self, event_id: int, ip: str | None) -> bool:
        """Зачитывает просмотр мероприятия, если он уникален для данной пары
        (event_id, ip) в окне VIEW_DEDUPE_TTL_SECONDS.

        Возвращает True, если просмотр прошёл проверку уникальности и был
        отправлен в очередь агрегации.
        """
        if ip is None:
            return False

        key = _view_dedupe_key(event_id, ip)
        try:
            # SET NX EX: атомарная проверка уникальности + TTL 5 минут
            first_in_window = await self.redis.set(
                key, "1", nx=True, ex=VIEW_DEDUPE_TTL_SECONDS
            )
        except RedisError:
            # Redis недоступен — не теряем просмотры полностью,
            # но и не считаем дубликаты вслепую: пропускаем только этот раз.
            logger.exception("Redis unavailable while deduplicating view of %s", event_id)
            return False

        if not first_in_window:
            return False  # такой просмотр уже был менее 5 минут назад

        # Просмотр уникален — отправляем в asyncio.Queue, фоновый воркер
        # агрегирует его по мероприятиям и запишет в БД одним обновлением счётчика
        view_event_queue.add_view(event_id)
        return True

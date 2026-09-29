from taskiq import SimpleRetryMiddleware, TaskiqScheduler
from taskiq.middlewares.taskiq_admin_middleware import TaskiqAdminMiddleware
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_redis import RedisStreamBroker

from samokat.infrastructure.tasks.config import settings


broker_async = RedisStreamBroker(
    url=settings.redis.url,
    queue_name="async",
    socket_timeout=None,
).with_middlewares(
    TaskiqAdminMiddleware(
        url="http://samokat-taskiq-admin:3000",
        api_token="supersecret",
        taskiq_broker_name="samokat-async",
    ),
)

broker_cpu = RedisStreamBroker(
    url=settings.redis.url,
    queue_name="cpu",
    socket_timeout=None,
    xread_count=1,
).with_middlewares(
    SimpleRetryMiddleware(types_of_exceptions=(Exception,)),
    TaskiqAdminMiddleware(
        url="http://samokat-taskiq-admin:3000",
        api_token="supersecret",
        taskiq_broker_name="samokat-cpu",
    ),
)

scheduler = TaskiqScheduler(
    broker=broker_async,
    sources=[LabelScheduleSource(broker=broker_async)],
)

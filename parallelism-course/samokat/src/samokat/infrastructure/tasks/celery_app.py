from celery import Celery

from samokat.infrastructure.tasks.config import settings

celery_app = Celery(
    broker=settings.redis.url,
    include=["samokat.infrastructure.tasks.celery_tasks"],
)

celery_app.conf.update(
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    beat_schedule={
        "sync_darkstore_products_and_prices-every-5-minutes": {
            "task": "sync_darkstore_products_and_prices",
            "schedule": 60 * 5,
        },
    },
    task_routes={
        "generate_order_report": {"queue": "critical"},
        "sync_darkstore_products_and_prices": {"queue": "basic"},
    },
)

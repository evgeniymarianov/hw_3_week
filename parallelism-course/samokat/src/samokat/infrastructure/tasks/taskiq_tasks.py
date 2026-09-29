import logging
from datetime import timedelta

from dishka import Scope

from samokat.infrastructure.tasks.config import settings
from samokat.infrastructure.tasks.taskiq_app import broker_async, broker_cpu
from samokat.ioc import create_container
from samokat.services.darkstore_sync import DarkstoreSyncService
from samokat.services.reports import ReportService

logger = logging.getLogger(__name__)


@broker_async.task(
    task_name="sync_darkstore_products_and_prices",
    schedule=[
        {
            "schedule_id": "sync_darkstore_products_and_prices-every-5-seconds",
            "interval": timedelta(seconds=5),
        }
    ],
)
async def sync_darkstore_products_and_prices() -> None:
    container = create_container(settings)
    logger.info("Darkstore products sync started")
    async with container(scope=Scope.REQUEST) as request_container:
        service = await request_container.get(DarkstoreSyncService)
        await service.sync_products_and_prices()
    logger.info("Darkstore products sync finished")


@broker_cpu.task(
    task_name="generate_order_report",
    max_retries=2,
    retry_on_error=True,
)
async def generate_order_report(report_id: str) -> None:
    container = create_container(settings)
    logger.info("Report started")
    async with container(scope=Scope.REQUEST) as request_container:
        service = await request_container.get(ReportService)
        await service.generate_orders_report(report_id)
    logger.info("Report finished")

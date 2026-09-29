import asyncio
import logging
from contextlib import asynccontextmanager

from dishka import AsyncContainer, Scope
from fastapi import FastAPI
from faststream.kafka import KafkaBroker

from samokat.infrastructure.clickhouse.queue import ClickhouseEventQueue
from samokat.services.darkstore_sync import DarkstoreSyncService

logger = logging.getLogger(__name__)


def create_lifespan(container: AsyncContainer):
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        logger.info("Samokat lifespan started")
        # darkstore_sync_task = asyncio.create_task(run_darkstore_sync_loop(container))
        ch_event_queue = await container.get(ClickhouseEventQueue)
        kafka_broker = await container.get(KafkaBroker)
        ch_event_queue.start()
        await kafka_broker.start()

        try:
            yield
        finally:
            # logger.info("Samokat shutdown started")
            # darkstore_sync_task.cancel()
            # await asyncio.gather(darkstore_sync_task, return_exceptions=True)
            # logger.info("Darkstore products sync task cancelled")
            await ch_event_queue.stop()
            await kafka_broker.stop()

    return lifespan


async def run_darkstore_sync_loop(container: AsyncContainer) -> None:
    while True:
        try:
            logger.info("Darkstore products sync started")
            async with container(scope=Scope.REQUEST) as request_container:
                service = await request_container.get(DarkstoreSyncService)
                await service.sync_products_and_prices()
            logger.info("Darkstore products sync finished")
        except Exception:
            logger.exception("Darkstore products sync failed")

        await asyncio.sleep(60)

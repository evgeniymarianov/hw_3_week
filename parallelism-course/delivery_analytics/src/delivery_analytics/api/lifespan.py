import logging
from contextlib import asynccontextmanager

from dishka import AsyncContainer
from fastapi import FastAPI
from faststream.kafka import KafkaBroker

logger = logging.getLogger(__name__)


def create_lifespan(container: AsyncContainer):
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        logger.info("Delivery analytics lifespan started")
        broker = await container.get(KafkaBroker)
        await broker.start()

        try:
            yield
        finally:
            logger.info("Delivery analytics shutdown started")
            await broker.stop()
            await container.close()

    return lifespan

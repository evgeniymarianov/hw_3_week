from collections.abc import AsyncIterator

from dishka import AsyncContainer, Provider, Scope, make_async_container, provide
from dishka.integrations.fastapi import FastapiProvider
from faststream.kafka import KafkaBroker

from delivery_analytics.config import (
    KafkaConfig,
    PostgresConfig,
    Settings,
)
from delivery_analytics.infrastructure.kafka.consumer import create_kafka_broker
from delivery_analytics.infrastructure.postgres.manager import (
    DatabaseManager,
    PostgresClient,
)
from delivery_analytics.infrastructure.websocket.manager import WebsocketManager
from delivery_analytics.services.tracking_aggregation import TrackingAggregationService
from delivery_analytics.services.websocket_gps_broadcaster import WebsocketGPSBroadcaster


class ConfigProvider(Provider):
    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self._settings = settings

    @provide(scope=Scope.APP)
    def get_settings(self) -> Settings:
        return self._settings

    @provide(scope=Scope.APP)
    def get_postgres_config(self, settings: Settings) -> PostgresConfig:
        return settings.postgres

    @provide(scope=Scope.APP)
    def get_kafka_config(self, settings: Settings) -> KafkaConfig:
        return settings.kafka


class PostgresProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_postgres(
        self,
        config: PostgresConfig,
    ) -> AsyncIterator[PostgresClient]:
        postgres = PostgresClient(config)

        yield postgres

        await postgres.close()

    @provide(scope=Scope.REQUEST)
    async def get_db(
        self,
        postgres: PostgresClient,
    ) -> AsyncIterator[DatabaseManager]:
        async with postgres.session() as db:
            yield db


class ServiceProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_tracking_aggregation_service(
        self,
        db: DatabaseManager,
        ws_broadcaster: WebsocketGPSBroadcaster,
    ) -> TrackingAggregationService:
        return TrackingAggregationService(
            db=db,
            ws_broadcaster=ws_broadcaster,
        )

    @provide(scope=Scope.REQUEST)
    def get_ws_broadcaster(
        self,
        ws_manager: WebsocketManager,
    ) -> WebsocketGPSBroadcaster:
        return WebsocketGPSBroadcaster(ws_manager=ws_manager)


class WebsocketInfrastructureProvider(Provider):
    @provide(scope=Scope.APP)
    def get_ws_manager(self) -> WebsocketManager:
        return WebsocketManager()


class KafkaProvider(Provider):
    @provide(scope=Scope.APP)
    def get_kafka_broker(
        self,
        config: KafkaConfig,
        container: AsyncContainer,
    ) -> KafkaBroker:
        return create_kafka_broker(config, container)


def create_container(settings: Settings):
    return make_async_container(
        ConfigProvider(settings),
        PostgresProvider(),
        ServiceProvider(),
        KafkaProvider(),
        WebsocketInfrastructureProvider(),
        FastapiProvider(),
    )

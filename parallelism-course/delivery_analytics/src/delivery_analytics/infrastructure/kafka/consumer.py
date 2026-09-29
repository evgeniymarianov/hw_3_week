from dishka import AsyncContainer, Scope
from faststream import AckPolicy
from faststream.kafka import KafkaBroker

from delivery_analytics.config import KafkaConfig
from delivery_analytics.infrastructure.kafka.schemas import DeliveryTrackingEvent
from delivery_analytics.services.tracking_aggregation import TrackingAggregationService


def create_kafka_broker(config: KafkaConfig, container: AsyncContainer):
    broker = KafkaBroker(
        bootstrap_servers=config.bootstrap_servers,
    )

    @broker.subscriber(
        config.tracking_topic,
        batch=True,
        group_id=config.group_id,
        auto_offset_reset="earliest",
        ack_policy=AckPolicy.NACK_ON_ERROR,
        max_records=200,
        batch_timeout_ms=500,
    )
    async def process_gps_events(messages: list[DeliveryTrackingEvent]):
        async with container(scope=Scope.REQUEST) as rq_container:
            tracking_service = await rq_container.get(TrackingAggregationService)
            await tracking_service.process(messages)

    return broker

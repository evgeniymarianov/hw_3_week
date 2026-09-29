from clickhouse_connect.driver import AsyncClient
from clickhouse_connect import get_async_client

from samokat.config import ClickHouseConfig
from samokat.infrastructure.clickhouse.schemas import UserEvent


class ClickHouseManager:
    def __init__(self, client: AsyncClient) -> None:
        self.client = client

    async def close(self) -> None:
        close_result = self.client.close()

        if close_result is not None:
            await close_result

    async def insert(self, table_name: str, columns: list[str], data: list):
        await self.client.insert(table_name, data, column_names=columns)

    async def insert_user_events(
        self,
        events: list[UserEvent]
    ) -> None:
        await self.insert(
            table_name="user_events",
            columns=[
                "user_id",
                "event",
                "category",
                "event_time",
            ],
            data=[
                [
                    event.user_id,
                    event.event,
                    event.category,
                    event.event_time,
                ] for event in events
            ],
        )


async def create_clickhouse_manager(
    config: ClickHouseConfig,
) -> ClickHouseManager:
    client = await get_async_client(
        host=config.host,
        port=config.port,
        username=config.username,
        password=config.password.get_secret_value(),
        database=config.database,
        secure=config.secure,
        compress=config.compress,
    )

    return ClickHouseManager(client)

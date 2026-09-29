from redis.asyncio import Redis

from samokat.config import RedisConfig


class RedisManager:
    def __init__(self, redis: Redis) -> None:
        self.client = redis

    async def close(self) -> None:
        await self.client.aclose()


def create_redis_manager(config: RedisConfig) -> RedisManager:
    redis = Redis.from_url(
        config.url,
        decode_responses=True,
    )

    return RedisManager(redis)

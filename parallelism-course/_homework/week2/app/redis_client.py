from redis.asyncio import Redis

from app.config import REDIS_URL

redis_client: Redis = Redis.from_url(REDIS_URL, decode_responses=True)
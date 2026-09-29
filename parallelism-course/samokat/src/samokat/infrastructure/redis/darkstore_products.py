from samokat.infrastructure.redis.manager import RedisManager


class DarkstoreProductsCache:
    def __init__(
        self,
        redis: RedisManager,
    ) -> None:
        self._client = redis.client

    async def get_product_ids(
        self,
        darkstore_id: str,
    ) -> list[int] | None:
        key = self._get_key(darkstore_id)

        key_exists = await self._client.exists(key)

        if not key_exists:
            return None

        values = await self._client.smembers(key)

        return [int(value) for value in values]

    async def set_product_ids(
        self,
        darkstore_id: str,
        product_ids: list[int],
        ttl: int = 1_800,
    ) -> None:
        key = self._get_key(darkstore_id)

        await self._client.delete(key)

        if product_ids:
            await self._client.sadd(
                key,
                *[str(product_id) for product_id in product_ids],
            )

        await self._client.expire(key, ttl)

    def _get_key(
        self,
        darkstore_id: str,
    ) -> str:
        return f"darkstore_products:{darkstore_id}"

import json

from samokat.application.dto import CategoryData, ProductCardData
from samokat.infrastructure.redis.manager import RedisManager


class ProductCache:
    def __init__(
        self,
        redis: RedisManager,
    ) -> None:
        self._client = redis.client

    def _get_product_key(self, product_id: int) -> str:
        return f"product_card:{product_id}"

    def _get_categories_key(self) -> str:
        return "categories"

    async def get_categories(
        self,
    ) -> list[CategoryData] | None:
        res = await self._client.get(self._get_categories_key())

        if res is None:
            return None

        return [CategoryData.model_validate(val) for val in json.loads(res)]

    async def set_categories(
        self,
        categories: list[CategoryData],
        ttl: int = 300,
    ) -> None:
        await self._client.set(
            self._get_categories_key(),
            json.dumps([cat.model_dump() for cat in categories]),
            ex=ttl,
        )

    async def get_product_card(
        self,
        product_id: int,
    ) -> ProductCardData | None:
        value = await self._client.get(self._get_product_key(product_id))

        if value is None:
            return None

        return ProductCardData.model_validate_json(value)

    async def set_product_card(
        self,
        product_id: int,
        product_card: ProductCardData,
        ttl: int = 300,
    ) -> None:
        await self._client.set(
            self._get_product_key(product_id),
            product_card.model_dump_json(),
            ex=ttl,
        )

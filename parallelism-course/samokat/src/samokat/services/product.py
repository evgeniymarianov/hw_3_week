from samokat.domain.exceptions import ProductCardNotFoundError, UserAddressNotFoundError
from samokat.application.dto import CategoryData, ProductCardData, ProductData
from samokat.infrastructure.cache.local import InMemoryCache
from samokat.infrastructure.concurrency.singleflight import SingleFlight
from samokat.infrastructure.postgres.manager import DatabaseManager
from samokat.infrastructure.redis.darkstore_products import DarkstoreProductsCache
from samokat.infrastructure.redis.product_card_cache import ProductCache


class ProductService:
    def __init__(
        self,
        db: DatabaseManager,
        product_cache: ProductCache,
        darkstore_products_cache: DarkstoreProductsCache,
        singleflight: SingleFlight,
        local_cache: InMemoryCache,
    ) -> None:
        self.db = db
        self.product_cache = product_cache
        self.darkstore_products_cache = darkstore_products_cache
        self.singleflight = singleflight
        self.local_cache = local_cache

    async def get_categories(self) -> list[CategoryData]:
        categories_cached = await self.product_cache.get_categories()
        if categories_cached is not None:
            return categories_cached

        categories_db = await self.db.categories.get_categories()
        await self.product_cache.set_categories(categories_db)
        return categories_db

    async def get_product_card(
        self,
        product_id: int,
    ) -> ProductCardData:
        """Реализация с Singleflight"""
        product_cached_local = self.local_cache.get_product(product_id)
        if product_cached_local is not None:
            return product_cached_local

        product_cached = await self.product_cache.get_product_card(product_id)
        if product_cached is not None:
            return product_cached

        product = await self.singleflight.run(
            key=f"product_id:{product_id}",
            operation=self._load_product_card(product_id),
        )

        return product

    # async def get_product_card(
    #     self,
    #     product_id: int,
    # ) -> ProductCardData:
    #     """Старая реализация"""
    #     product_cached = await self.product_cache.get_product_card(product_id)
    #     if product_cached is not None:
    #         return product_cached
    #
    #     product = await self._load_product_card(product_id)
    #
    #     return product

    async def _load_product_card(self, product_id: int):
        product_from_db = await self.db.products.get_product_card(product_id)
        if product_from_db is None:
            raise ProductCardNotFoundError

        await self.product_cache.set_product_card(product_id, product_from_db)
        self.local_cache.set_product(product_from_db)
        return product_from_db

    async def get_category_products(
        self,
        user_id: int,
        category_id: int | None = None,
    ) -> list[ProductData]:
        user_address = await self.db.user_addresses.get_active_user_address(user_id)

        if user_address is None:
            raise UserAddressNotFoundError

        product_ids = await self._get_product_ids_for_darkstore(
            darkstore_id=user_address.darkstore_id,
        )

        return await self.db.products.get_products_by_ids(
            product_ids=product_ids,
            category_id=category_id,
        )

    async def _get_product_ids_for_darkstore(
        self,
        darkstore_id: str,
    ) -> list[int]:
        """Специальный метод для cache aside механики"""
        product_ids = await self.darkstore_products_cache.get_product_ids(
            darkstore_id=darkstore_id,
        )

        if product_ids is not None:
            return product_ids

        product_ids = await self.db.darkstore_products.get_product_ids(
            darkstore_id=darkstore_id,
        )
        await self.darkstore_products_cache.set_product_ids(
            darkstore_id=darkstore_id,
            product_ids=product_ids,
        )

        return product_ids

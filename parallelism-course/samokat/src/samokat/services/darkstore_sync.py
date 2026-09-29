from samokat.infrastructure.api_connectors.internal.darkstore import DarkstoreConnector
from samokat.infrastructure.api_connectors.schemas import DarkstoreProductData
from samokat.infrastructure.postgres.manager import DatabaseManager
from samokat.infrastructure.redis.darkstore_products import DarkstoreProductsCache


class DarkstoreSyncService:
    def __init__(
        self,
        db: DatabaseManager,
        darkstore_connector: DarkstoreConnector,
        darkstore_products_cache: DarkstoreProductsCache,
    ) -> None:
        self.db = db
        self.darkstore_connector = darkstore_connector
        self.darkstore_products_cache = darkstore_products_cache

    async def sync_products_and_prices(self) -> None:
        external_products = await self.darkstore_connector.get_products()
        product_ids_by_sku = {}

        for product in external_products:
            product_ids_by_sku[product.sku_id] = await self._sync_product(product)

        items_by_darkstore = await self.darkstore_connector.get_items_by_darkstore()

        for darkstore_id, darkstore_items in items_by_darkstore.items():
            product_ids = []

            for item in darkstore_items:
                product_id = product_ids_by_sku.get(item.sku_id)

                if product_id is None:
                    product_id = await self._sync_product(item)
                    product_ids_by_sku[item.sku_id] = product_id

                product_ids.append(product_id)

            await self.db.darkstore_products.set_darkstore_products(
                darkstore_id=darkstore_id,
                product_ids=product_ids,
            )
            await self.darkstore_products_cache.set_product_ids(
                darkstore_id=darkstore_id,
                product_ids=product_ids,
            )

        await self.db.commit()

    async def _sync_product(
        self,
        product: DarkstoreProductData,
    ) -> int:
        await self.db.categories.upsert_category(
            category_id=product.category_id,
            title=product.category_title,
        )

        return await self.db.products.upsert_product(
            darkstore_product_id=product.sku_id,
            category_id=product.category_id,
            title=product.title,
            description=product.description,
            price=product.price,
            is_active=product.is_active,
        )

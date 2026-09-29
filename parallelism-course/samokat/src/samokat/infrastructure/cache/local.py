from cachetools import TLRUCache

from samokat.application.dto import ProductCardData


class InMemoryCache:
    def __init__(self):
        self._products = TLRUCache(
            maxsize=1000,
            ttu=lambda key, value, now: now + value["ttl"],
        )

    def get_product(self, product_id) -> ProductCardData | None:
        return self._products.get(product_id, {}).get("data")

    def set_product(self, product: ProductCardData):
        self._products[product.id] = {
            "data": product,
            "ttl": 60,
        }

from samokat.infrastructure.api_connectors.base import BaseHTTPConnector
from samokat.infrastructure.api_connectors.schemas import (
    DarkstoreProductData,
    DarkstoreReservationData,
    DarkstoreReservationItemData,
)


class DarkstoreConnector(BaseHTTPConnector):
    async def get_products(self) -> list[DarkstoreProductData]:
        response = await self._request(
            "GET",
            "/products",
        )
        response.raise_for_status()

        return [DarkstoreProductData.model_validate(item) for item in response.json()]

    async def get_items_by_darkstore(self) -> dict[str, list[DarkstoreProductData]]:
        response = await self._request(
            "GET",
            "/darkstores/items",
        )
        response.raise_for_status()

        items_by_darkstore = response.json()["items_by_darkstore"]
        return {
            darkstore_id: [
                DarkstoreProductData.model_validate(item)
                for item in darkstore_items
            ]
            for darkstore_id, darkstore_items in items_by_darkstore.items()
        }

    async def get_suitable_darkstore(self, lat: float, lon: float):
        response = await self._request(
            "GET",
            "/darkstore/suitable",
            params={"lat": lat, "lon": lon},
        )
        response.raise_for_status()

        darkstore_id = response.json()
        return darkstore_id

    async def reserve_items(
        self,
        items: list[DarkstoreReservationItemData],
    ) -> DarkstoreReservationData:
        response = await self._request(
            "POST",
            "/reservations",
            json={"items": [item.model_dump() for item in items]},
        )
        response.raise_for_status()

        return DarkstoreReservationData.model_validate(response.json())

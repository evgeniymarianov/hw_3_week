from samokat.infrastructure.api_connectors.base import BaseHTTPConnector
from samokat.infrastructure.api_connectors.schemas import DeliveryData, DeliveryInfoData


class DeliveryConnector(BaseHTTPConnector):
    async def get_delivery_price(
        self,
        address: str,
        lat: float,
        lon: float,
    ) -> int:
        response = await self._request(
            "POST",
            "/deliveries/price",
            json={
                "address": address,
                "lat": lat,
                "lon": lon,
            },
        )
        response.raise_for_status()

        data = response.json()
        return data["price"]

    async def create_delivery(
        self,
        order_id: int,
        address: str,
        lat: float,
        lon: float,
        darkstore_id: str,
    ) -> DeliveryData:
        response = await self._request(
            "POST",
            "/deliveries",
            json={
                "order_id": order_id,
                "address": address,
                "lat": lat,
                "lon": lon,
                "darkstore_id": darkstore_id,
            },
        )
        response.raise_for_status()

        data = response.json()

        return DeliveryData(
            delivery_id=data["delivery_id"],
            order_id=order_id,
            status=data["status"],
        )

    async def get_delivery_info(
        self,
        delivery_id: str,
    ) -> DeliveryInfoData | None:
        response = await self._request(
            "GET",
            f"/deliveries/{delivery_id}",
        )

        if response.status_code == 404:
            return None

        response.raise_for_status()

        data = response.json()

        return DeliveryInfoData(
            delivery_id=delivery_id,
            status=data["status"],
            estimated_delivery_at=data.get("estimated_delivery_at"),
        )

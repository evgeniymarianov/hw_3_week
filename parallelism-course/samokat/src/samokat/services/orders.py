import asyncio

from samokat.domain.enums import DeliveryStatus, OrderStatus
from samokat.domain.exceptions import (
    CartIsEmptyError,
    OrderNotFoundError,
    UserAddressNotFoundError,
)
from samokat.infrastructure.api_connectors.internal.delivery import DeliveryConnector
from samokat.infrastructure.api_connectors.internal.darkstore import DarkstoreConnector
from samokat.infrastructure.api_connectors.schemas import (
    DarkstoreReservationData,
    DarkstoreReservationItemData,
)
from samokat.infrastructure.postgres.manager import DatabaseManager
from samokat.config import Settings
from samokat.application.dto import (
    OrderCreateData,
    OrderData,
    OrderDeliveryData,
    OrderDetailsData,
    OrderItemCreateData,
    OrderItemData,
    OrderPreviewData,
    PreorderCartItemData,
    UserAddressData,
)
from samokat.services.profiling import line_profile_async


# from samokat.services.profiling import line_profile_async

settings = Settings()


class OrderService:
    def __init__(
        self,
        db: DatabaseManager,
        darkstore_connector: DarkstoreConnector,
        delivery_connector: DeliveryConnector,
    ) -> None:
        self.db = db
        self.darkstore_connector = darkstore_connector
        self.delivery_connector = delivery_connector

    async def create_order(
        self,
        user_id: int,
        darkstore_reservation_id: str,
    ) -> OrderCreateData:
        user_address = await self._get_active_user_address(user_id)
        cart_items = await self._get_cart_items(user_id)

        products_price = self._calculate_products_price(cart_items)
        delivery_price = await self.delivery_connector.get_delivery_price(
            address=user_address.address_text,
            lat=user_address.lat,
            lon=user_address.lon,
        )
        total_price = products_price + delivery_price

        order_id = await self.db.orders.add_order(
            user_id=user_id,
            user_address_id=user_address.id,
            status=OrderStatus.PAID,
            address_text=user_address.address_text,
            darkstore_id=user_address.darkstore_id,
            darkstore_reservation_id=darkstore_reservation_id,
            total_price=total_price,
        )
        await self.db.orders.add_order_items(
            order_id=order_id,
            items=self._get_order_items_for_create(cart_items),
        )

        delivery = await self.delivery_connector.create_delivery(
            order_id=order_id,
            address=user_address.address_text,
            lat=user_address.lat,
            lon=user_address.lon,
            darkstore_id=user_address.darkstore_id,
        )
        await self.db.orders.set_delivery_id(
            order_id=order_id,
            delivery_id=delivery.delivery_id,
        )
        await self.db.cart_items.clear_user_cart(user_id)
        await self.db.commit()

        return OrderCreateData(
            order_id=order_id,
            status=OrderStatus.PAID,
            total_price=total_price,
            delivery_id=delivery.delivery_id,
        )

    @line_profile_async(enabled=settings.profiling.line_profiler_enabled)
    async def preview_order(
        self,
        user_id: int,
    ) -> OrderPreviewData:
        async with asyncio.TaskGroup() as tg:
            task_user_address = tg.create_task(
                self._get_active_user_address(user_id),
                name="get_active_user_address",
            )
            task_cart_items = tg.create_task(
                self._get_cart_items(user_id),
                name="get_cart_items",
            )

        user_address = task_user_address.result()
        cart_items = task_cart_items.result()

        _ = [i**i for i in range(3001)]

        async with asyncio.TaskGroup() as tg:
            reservation_task = tg.create_task(
                self._reserve_cart_items(cart_items),
                name="reserve_cart_items",
            )
            delivery_price_task = tg.create_task(
                self.delivery_connector.get_delivery_price(
                    address=user_address.address_text,
                    lat=user_address.lat,
                    lon=user_address.lon,
                ),
                name="get_delivery_price",
            )

        reservation = reservation_task.result()
        delivery_price = delivery_price_task.result()

        products_price = self._calculate_products_price(cart_items)

        return OrderPreviewData(
            items=self._get_order_items(cart_items),
            products_price=products_price,
            delivery_price=delivery_price,
            total_price=products_price + delivery_price,
            darkstore_reservation_id=reservation.reservation_id,
        )

    async def _reserve_cart_items(
        self,
        cart_items: list[PreorderCartItemData],
    ) -> DarkstoreReservationData:
        return await self.darkstore_connector.reserve_items(
            [
                DarkstoreReservationItemData(
                    sku_id=item.darkstore_product_id,
                    quantity=item.quantity,
                )
                for item in cart_items
            ],
        )

    async def _get_active_user_address(
        self,
        user_id: int,
    ) -> UserAddressData:
        async with self.db.transaction() as db:
            user_address = await db.user_addresses.get_active_user_address(user_id)

            if user_address is None:
                raise UserAddressNotFoundError

            return user_address

    async def _get_cart_items(
        self,
        user_id: int,
    ) -> list[PreorderCartItemData]:
        async with self.db.transaction() as db:
            cart_items = await db.cart_items.get_user_cart_items(user_id)

            if not cart_items:
                raise CartIsEmptyError

            return cart_items

    async def get_orders(
        self,
        user_id: int,
    ) -> list[OrderData]:
        return await self.db.orders.get_orders(user_id)

    async def get_order(
        self,
        order_id: int,
    ) -> OrderDetailsData:
        order = await self.db.orders.get_order(order_id)

        if order is None:
            raise OrderNotFoundError

        if order.status == OrderStatus.COMPLETED or order.delivery_id is None:
            return order

        delivery = await self.delivery_connector.get_delivery_info(
            order.delivery_id,
        )

        if delivery is None:
            return order

        if delivery.status == DeliveryStatus.COMPLETED:
            await self.db.orders.set_order_status(
                order_id=order.id,
                status=OrderStatus.COMPLETED,
            )
            await self.db.commit()
            return order.model_copy(
                update={"status": OrderStatus.COMPLETED},
            )

        return order.model_copy(
            update={
                "delivery": OrderDeliveryData(
                    delivery_id=delivery.delivery_id,
                    status=delivery.status,
                    estimated_delivery_at=delivery.estimated_delivery_at,
                ),
            },
        )

    def _get_order_items(
        self,
        cart_items: list[PreorderCartItemData],
    ) -> list[OrderItemData]:
        return [
            OrderItemData(
                product_id=item.product_id,
                product_title=item.title,
                price=item.price,
                quantity=item.quantity,
                total_price=item.price * item.quantity,
            )
            for item in cart_items
        ]

    def _get_order_items_for_create(
        self,
        cart_items: list[PreorderCartItemData],
    ) -> list[OrderItemCreateData]:
        return [
            OrderItemCreateData(
                product_id=item.product_id,
                product_title=item.title,
                price=item.price,
                quantity=item.quantity,
            )
            for item in cart_items
        ]

    def _calculate_products_price(
        self,
        cart_items: list[PreorderCartItemData],
    ) -> int:
        return sum(item.price * item.quantity for item in cart_items)

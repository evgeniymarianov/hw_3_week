from sqlalchemy import insert, select, update

from samokat.application.dto import (
    OrderData,
    OrderDetailsData,
    OrderItemCreateData,
    OrderItemData,
    OrderReportRowData,
)
from samokat.infrastructure.postgres.models import OrderItemModel, OrderModel
from samokat.infrastructure.postgres.repositories.base import BaseRepo


class OrderRepo(BaseRepo):
    async def add_order(
        self,
        user_id: int,
        user_address_id: int,
        status: str,
        address_text: str,
        darkstore_id: str,
        darkstore_reservation_id: str,
        total_price: int,
    ) -> int:
        query = (
            insert(OrderModel)
            .values(
                user_id=user_id,
                user_address_id=user_address_id,
                status=status,
                address_text=address_text,
                darkstore_id=darkstore_id,
                darkstore_reservation_id=darkstore_reservation_id,
                total_price=total_price,
            )
            .returning(OrderModel.id)
        )

        order_id = await self.session.scalar(query)
        return order_id

    async def add_order_items(
        self,
        order_id: int,
        items: list[OrderItemCreateData],
    ) -> None:
        query = insert(OrderItemModel).values(
            [
                {
                    "order_id": order_id,
                    "product_id": item.product_id,
                    "product_title": item.product_title,
                    "price": item.price,
                    "quantity": item.quantity,
                }
                for item in items
            ]
        )

        await self.session.execute(query)

    async def set_delivery_id(
        self,
        order_id: int,
        delivery_id: str,
    ) -> None:
        query = (
            update(OrderModel)
            .where(OrderModel.id == order_id)
            .values(delivery_id=delivery_id)
        )

        await self.session.execute(query)

    async def set_order_status(
        self,
        order_id: int,
        status: str,
    ) -> None:
        query = (
            update(OrderModel).where(OrderModel.id == order_id).values(status=status)
        )

        await self.session.execute(query)

    async def get_orders(
        self,
        user_id: int,
    ) -> list[OrderData]:
        query = (
            select(OrderModel)
            .where(OrderModel.user_id == user_id)
            .order_by(OrderModel.id.desc())
        )

        resp = await self.session.scalars(query)
        orders = resp.all()

        return [
            OrderData(
                id=order.id,
                status=order.status,
                address_text=order.address_text,
                total_price=order.total_price,
                delivery_id=order.delivery_id,
            )
            for order in orders
        ]

    async def get_order(
        self,
        order_id: int,
    ) -> OrderDetailsData | None:
        query = select(OrderModel).where(OrderModel.id == order_id)
        resp = await self.session.scalars(query)
        order = resp.one_or_none()

        if order is None:
            return None

        items = await self.get_order_items(order_id)

        return OrderDetailsData(
            id=order.id,
            status=order.status,
            address_text=order.address_text,
            total_price=order.total_price,
            delivery_id=order.delivery_id,
            items=items,
        )

    async def get_order_items(
        self,
        order_id: int,
    ) -> list[OrderItemData]:
        query = select(OrderItemModel).where(
            OrderItemModel.order_id == order_id,
        )

        resp = await self.session.scalars(query)
        items = resp.all()

        return [
            OrderItemData(
                product_id=item.product_id,
                product_title=item.product_title,
                price=item.price,
                quantity=item.quantity,
                total_price=item.price * item.quantity,
            )
            for item in items
        ]

    async def get_report_rows(self, user_id: int) -> list[OrderReportRowData]:
        query = (
            select(
                OrderModel.id.label("order_id"),
                OrderModel.status,
                OrderModel.address_text,
                OrderModel.total_price,
                OrderModel.created_at,
                OrderItemModel.product_title,
                OrderItemModel.price,
                OrderItemModel.quantity,
            )
            .join(OrderItemModel, OrderItemModel.order_id == OrderModel.id)
            .where(OrderModel.user_id == user_id)
            .order_by(OrderModel.id.desc(), OrderItemModel.id.asc())
        )

        resp = await self.session.execute(query)
        rows = resp.all()

        return [
            OrderReportRowData(
                order_id=row.order_id,
                status=row.status,
                address_text=row.address_text,
                total_price=row.total_price,
                created_at=row.created_at,
                product_title=row.product_title,
                price=row.price,
                quantity=row.quantity,
                item_total_price=row.price * row.quantity,
            )
            for row in rows
        ]

import logging

from samokat.application.dto import CartData, CartItemDetailsData
from samokat.infrastructure.clickhouse.queue import ClickhouseEventQueue
from samokat.infrastructure.postgres.manager import DatabaseManager

logger = logging.getLogger(__name__)


class CartService:
    def __init__(
        self,
        db: DatabaseManager,
        events: ClickhouseEventQueue,
    ) -> None:
        self.db = db
        self.events = events

    async def add_item(
        self,
        user_id: int,
        product_id: int,
        quantity: int,
    ) -> None:
        category = await self.db.products.get_product_category_title(product_id)

        await self.db.cart_items.add_cart_item(
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
        )
        await self.db.commit()

        event_category = category or "unknown"
        self.events.add_user_event(user_id, "card_added_item", event_category)

    async def update_item_quantity(
        self,
        user_id: int,
        product_id: int,
        quantity: int,
    ) -> None:
        await self.db.cart_items.update_cart_item_quantity(
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
        )
        await self.db.commit()

    async def get_cart(
        self,
        user_id: int,
    ) -> CartData:
        cart_items = await self.db.cart_items.get_user_cart_items(user_id)
        items = [
            CartItemDetailsData(
                product_id=item.product_id,
                title=item.title,
                price=item.price,
                quantity=item.quantity,
                total_price=item.price * item.quantity,
            )
            for item in cart_items
        ]

        return CartData(
            items=items,
            products_price=sum(item.total_price for item in items),
        )

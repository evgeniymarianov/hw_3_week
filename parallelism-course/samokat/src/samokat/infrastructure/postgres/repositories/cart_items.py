from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert

from samokat.application.dto import PreorderCartItemData
from samokat.infrastructure.postgres.models import CartItemModel, ProductModel
from samokat.infrastructure.postgres.repositories.base import BaseRepo


class CartItemRepo(BaseRepo):
    async def add_cart_item(
        self,
        user_id: int,
        product_id: int,
        quantity: int,
    ) -> None:
        query = (
            insert(CartItemModel)
            .values(
                user_id=user_id,
                product_id=product_id,
                quantity=quantity,
            )
            .on_conflict_do_update(
                index_elements=[
                    CartItemModel.user_id,
                    CartItemModel.product_id,
                ],
                set_={
                    "quantity": CartItemModel.quantity + quantity,
                },
            )
        )

        await self.session.execute(query)

    async def update_cart_item_quantity(
        self,
        user_id: int,
        product_id: int,
        quantity: int,
    ) -> None:
        if quantity <= 0:
            query = delete(CartItemModel).where(
                CartItemModel.user_id == user_id,
                CartItemModel.product_id == product_id,
            )
            await self.session.execute(query)
            return

        query = (
            update(CartItemModel)
            .where(
                CartItemModel.user_id == user_id,
                CartItemModel.product_id == product_id,
            )
            .values(quantity=quantity)
        )

        await self.session.execute(query)

    async def get_user_cart_items(
        self,
        user_id: int,
    ) -> list[PreorderCartItemData]:
        """Получение всей корзины с актуальными ценами"""
        query = (
            select(
                ProductModel.id.label("product_id"),
                ProductModel.darkstore_product_id,
                ProductModel.title,
                ProductModel.price,
                CartItemModel.quantity,
            )
            .join(ProductModel, ProductModel.id == CartItemModel.product_id)
            .where(CartItemModel.user_id == user_id)
        )

        resp = await self.session.execute(query)
        rows = resp.all()

        return [
            PreorderCartItemData(
                product_id=row.product_id,
                darkstore_product_id=row.darkstore_product_id,
                title=row.title,
                price=row.price,
                quantity=row.quantity,
            )
            for row in rows
        ]

    async def clear_user_cart(
        self,
        user_id: int,
    ) -> None:
        query = delete(CartItemModel).where(
            CartItemModel.user_id == user_id,
        )

        await self.session.execute(query)

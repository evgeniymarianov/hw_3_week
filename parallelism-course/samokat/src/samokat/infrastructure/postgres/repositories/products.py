from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert

from samokat.application.dto import ProductCardData, ProductData
from samokat.infrastructure.postgres.models import CategoryModel, ProductModel
from samokat.infrastructure.postgres.repositories.base import BaseRepo


class ProductRepo(BaseRepo):
    async def upsert_product(
        self,
        darkstore_product_id: str,
        category_id: int,
        title: str,
        description: str | None,
        price: int,
        is_active: bool,
    ) -> int:
        query = (
            insert(ProductModel)
            .values(
                darkstore_product_id=darkstore_product_id,
                category_id=category_id,
                title=title,
                description=description,
                price=price,
                is_active=is_active,
            )
            .on_conflict_do_update(
                index_elements=[ProductModel.darkstore_product_id],
                set_={
                    "category_id": category_id,
                    "title": title,
                    "description": description,
                    "price": price,
                    "is_active": is_active,
                },
            )
            .returning(ProductModel.id)
        )

        product_id = await self.session.scalar(query)
        return product_id

    async def get_products_by_ids(
        self,
        product_ids: list[int],
        category_id: int | None = None,
    ) -> list[ProductData]:
        if not product_ids:
            return []

        query = select(ProductModel).where(
            ProductModel.id.in_(product_ids),
            ProductModel.is_active.is_(True),
        )

        if category_id is not None:
            query = query.where(ProductModel.category_id == category_id)

        resp = await self.session.scalars(query)
        products = resp.all()

        return [
            ProductData(
                id=product.id,
                category_id=product.category_id,
                title=product.title,
                price=product.price,
                is_active=product.is_active,
            )
            for product in products
        ]

    async def get_product_card(
        self,
        product_id: int,
    ) -> ProductCardData | None:
        # Код для имитации сетевой задержки с урока:
        # print("GOING TO DATABASE")
        # delay = select(func.pg_sleep(0.1)).cte("delay")
        # query = select(ProductModel).select_from(ProductModel, delay).where...
        query = select(ProductModel).where(
            ProductModel.id == product_id,
            ProductModel.is_active.is_(True),
        )

        resp = await self.session.scalars(query)
        product = resp.one_or_none()

        if product is None:
            return None

        return ProductCardData(
            id=product.id,
            category_id=product.category_id,
            title=product.title,
            description=product.description,
            price=product.price,
            is_active=product.is_active,
        )

    async def get_product_category_title(
        self,
        product_id: int,
    ) -> str | None:
        query = (
            select(CategoryModel.title)
            .select_from(ProductModel)
            .join(CategoryModel, CategoryModel.id == ProductModel.category_id)
            .where(ProductModel.id == product_id)
        )

        return await self.session.scalar(query)

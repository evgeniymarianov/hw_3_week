from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from samokat.application.dto import CategoryData
from samokat.infrastructure.postgres.models import CategoryModel
from samokat.infrastructure.postgres.repositories.base import BaseRepo


class ProductCategoryRepo(BaseRepo):
    async def upsert_category(
        self,
        category_id: int,
        title: str,
    ) -> None:
        query = (
            insert(CategoryModel)
            .values(
                id=category_id,
                title=title,
            )
            .on_conflict_do_update(
                index_elements=[CategoryModel.id],
                set_={"title": title},
            )
        )

        await self.session.execute(query)

    async def get_categories(self) -> list[CategoryData]:
        query = select(CategoryModel)

        resp = await self.session.scalars(query)
        categories = resp.all()

        return [
            CategoryData(
                id=category.id,
                title=category.title,
            )
            for category in categories
        ]

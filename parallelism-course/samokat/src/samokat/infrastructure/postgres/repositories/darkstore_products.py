from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert

from samokat.infrastructure.postgres.models import DarkstoreProductModel
from samokat.infrastructure.postgres.repositories.base import BaseRepo


class DarkstoreProductRepo(BaseRepo):
    async def set_darkstore_products(
        self,
        darkstore_id: str,
        product_ids: list[int],
    ) -> None:
        disable_query = (
            update(DarkstoreProductModel)
            .where(DarkstoreProductModel.darkstore_id == darkstore_id)
            .values(
                is_available=False,
                updated_at=func.now(),
            )
        )
        await self.session.execute(disable_query)

        if not product_ids:
            return

        query = (
            insert(DarkstoreProductModel)
            .values(
                [
                    {
                        "darkstore_id": darkstore_id,
                        "product_id": product_id,
                        "is_available": True,
                    }
                    for product_id in product_ids
                ],
            )
            .on_conflict_do_update(
                index_elements=[
                    DarkstoreProductModel.darkstore_id,
                    DarkstoreProductModel.product_id,
                ],
                set_={
                    "is_available": True,
                    "updated_at": func.now(),
                },
            )
        )

        await self.session.execute(query)

    async def get_product_ids(
        self,
        darkstore_id: str,
    ) -> list[int]:
        query = select(DarkstoreProductModel.product_id).where(
            DarkstoreProductModel.darkstore_id == darkstore_id,
            DarkstoreProductModel.is_available.is_(True),
        )

        resp = await self.session.scalars(query)

        return list(resp.all())

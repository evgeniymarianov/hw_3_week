from dishka.integrations.fastapi import (
    DishkaRoute,
    FromDishka,
)
from fastapi import APIRouter

from samokat.api.dependencies import UserIdDep
from samokat.application.dto import CategoryData, ProductCardData, ProductData
from samokat.services.product import ProductService

router = APIRouter(prefix="/products", route_class=DishkaRoute, tags=["Продукты"])


@router.get("/categories")
async def get_categories(
    service: FromDishka[ProductService],
) -> list[CategoryData]:
    return await service.get_categories()


@router.get("/")
async def get_products(
    user_id: UserIdDep,
    service: FromDishka[ProductService],
    category_id: int | None = None,
) -> list[ProductData]:
    return await service.get_category_products(
        user_id=user_id,
        category_id=category_id,
    )


@router.get("/{product_id}")
async def get_product(
    product_id: int,
    service: FromDishka[ProductService],
) -> ProductCardData:
    return await service.get_product_card(product_id)

from typing import Annotated

from dishka.integrations.fastapi import (
    DishkaRoute,
    FromDishka,
)
from fastapi import APIRouter, Body

from samokat.api.dependencies import UserIdDep
from samokat.application.dto import CartData
from samokat.services.cart import CartService

router = APIRouter(prefix="/cart", route_class=DishkaRoute, tags=["Корзина"])


@router.post("/items/{product_id}")
async def change_item_quantity(
    product_id: int,
    quantity: Annotated[int, Body(embed=True)],
    user_id: UserIdDep,
    service: FromDishka[CartService],
) -> dict[str, str]:
    await service.update_item_quantity(
        user_id=user_id,
        product_id=product_id,
        quantity=quantity,
    )

    return {"message": "Количество товара изменено"}


@router.post("/")
async def add_product_to_cart(
    product_id: Annotated[int, Body(embed=True)],
    user_id: UserIdDep,
    service: FromDishka[CartService],
    quantity: Annotated[int, Body(embed=True)] = 1,
) -> dict[str, str]:
    await service.add_item(
        user_id=user_id,
        product_id=product_id,
        quantity=quantity,
    )

    return {"message": "Товар добавлен в корзину"}


@router.get("/items")
async def get_cart(
    user_id: UserIdDep,
    service: FromDishka[CartService],
) -> CartData:
    return await service.get_cart(user_id)

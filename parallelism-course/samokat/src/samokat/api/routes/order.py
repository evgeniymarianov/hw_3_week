from typing import Annotated

from dishka.integrations.fastapi import (
    DishkaRoute,
    FromDishka,
)
from fastapi import APIRouter, Body

from samokat.api.dependencies import UserIdDep
from samokat.services.orders import OrderService
from samokat.application.dto import (
    OrderCreateData,
    OrderData,
    OrderDetailsData,
    OrderPreviewData,
)

router = APIRouter(prefix="/orders", route_class=DishkaRoute, tags=["Заказы"])


@router.get("/")
async def get_my_orders(
    user_id: UserIdDep,
    service: FromDishka[OrderService],
) -> list[OrderData]:
    return await service.get_orders(user_id)


@router.post("/preview")
async def preview_current_order(
    user_id: UserIdDep,
    service: FromDishka[OrderService],
) -> OrderPreviewData:
    return await service.preview_order(user_id)


@router.post("/")
async def create_order(
    darkstore_reservation_id: Annotated[str, Body(embed=True)],
    user_id: UserIdDep,
    service: FromDishka[OrderService],
) -> OrderCreateData:
    return await service.create_order(
        user_id=user_id,
        darkstore_reservation_id=darkstore_reservation_id,
    )


@router.get("/{order_id}")
async def get_order(
    order_id: int,
    service: FromDishka[OrderService],
) -> OrderDetailsData:
    return await service.get_order(order_id)

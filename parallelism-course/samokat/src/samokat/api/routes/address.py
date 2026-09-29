from typing import Annotated

from dishka.integrations.fastapi import (
    DishkaRoute,
    FromDishka,
)
from fastapi import APIRouter, Body

from samokat.api.dependencies import UserIdDep
from samokat.application.dto import AddressSuggestionData, UserAddressData
from samokat.services.addresses import AddressService

router = APIRouter(prefix="/addresses", route_class=DishkaRoute, tags=["Адрес"])


@router.get("/suggestions")
async def get_address_suggestions(
    query: str,
    service: FromDishka[AddressService],
) -> list[AddressSuggestionData]:
    return await service.suggest_addresses(query)


@router.post("/")
async def add_address(
    selected_address_id: Annotated[str, Body(embed=True)],
    user_id: UserIdDep,
    service: FromDishka[AddressService],
) -> dict[str, str]:
    await service.create_user_address(
        user_id=user_id,
        selected_address_id=selected_address_id,
    )

    return {"message": "Адрес добавлен"}


@router.put("/")
async def change_address(
    address_id: Annotated[int, Body(embed=True)],
    user_id: UserIdDep,
    service: FromDishka[AddressService],
) -> dict[str, str]:
    await service.select_user_address(
        user_id=user_id,
        address_id=address_id,
    )

    return {"message": "Адрес изменен"}


@router.get("/active")
async def get_active_address(
    user_id: UserIdDep,
    service: FromDishka[AddressService],
) -> UserAddressData | None:
    return await service.get_active_user_address(user_id)

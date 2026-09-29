from typing import Annotated

from fastapi import APIRouter, Body
from dishka.integrations.fastapi import (
    DishkaRoute,
    FromDishka,
)
from pydantic import BaseModel, SecretStr

from samokat.api.dependencies import UserIdDep
from samokat.application.dto import User
from samokat.services.auth import AuthService
from samokat.services.users import UserService

router = APIRouter(prefix="/auth", route_class=DishkaRoute, tags=["Авторизация"])


class UserRegisterRequestSchema(BaseModel):
    username: str
    password: SecretStr


class UserLoginRequestSchema(BaseModel):
    username: str
    password: SecretStr


@router.post("/register")
async def register_user(
    data: UserRegisterRequestSchema,
    service: FromDishka[AuthService],
):
    await service.register_new_user(
        username=data.username,
        plain_password=data.password.get_secret_value(),
    )
    return {"message": "Вы успешно зарегистрированы"}


@router.post("/login")
async def login_user(
    data: UserLoginRequestSchema,
    service: FromDishka[AuthService],
):
    new_token_pair = await service.login_user(
        username=data.username,
        plain_password=data.password.get_secret_value(),
    )
    return new_token_pair


@router.post("/refresh")
async def refresh_tokens(
    refresh_token: Annotated[str, Body(embed=True)],
    service: FromDishka[AuthService],
):
    new_token_pair = await service.refresh_token_pair(refresh_token)
    return new_token_pair


@router.get("/users/me")
async def get_current_user(
    user_id: UserIdDep,
    service: FromDishka[UserService],
) -> User:
    return await service.get_user(user_id)

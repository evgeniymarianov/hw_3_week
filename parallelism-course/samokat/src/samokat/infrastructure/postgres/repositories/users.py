from sqlalchemy import insert, select

from samokat.application.dto import User
from samokat.infrastructure.postgres.models import UserModel
from samokat.infrastructure.postgres.repositories.base import BaseRepo
from samokat.application.dto import UserAuthData


class UserRepo(BaseRepo):
    async def add_user(
        self,
        username: str,
        hashed_password: str,
    ) -> int:
        query = (
            insert(UserModel)
            .values(
                username=username,
                hashed_password=hashed_password,
            )
            .returning(UserModel.id)
        )

        return await self.session.scalar(query)

    async def get_user_hashed_password(self, username: str):
        query = select(UserModel.id, UserModel.hashed_password).filter_by(
            username=username
        )

        resp = await self.session.execute(query)
        row = resp.one_or_none()

        if row is None:
            return UserAuthData(
                user_id=None,
                hashed_password=None,
            )

        return UserAuthData(
            user_id=row.id,
            hashed_password=row.hashed_password,
        )

    async def get_user(self, user_id: int) -> User | None:
        query = select(
            UserModel.id,
            UserModel.username,
        ).where(UserModel.id == user_id)
        resp = await self.session.execute(query)
        row = resp.one_or_none()
        if not row:
            return None
        return User(
            id=row.id,
            username=row.username,
        )

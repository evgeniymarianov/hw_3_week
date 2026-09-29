from sqlalchemy import insert, select, update

from samokat.application.dto import UserAddressData
from samokat.infrastructure.postgres.models import UserAddressModel
from samokat.infrastructure.postgres.repositories.base import BaseRepo


class UserAddressRepo(BaseRepo):
    async def add_address(
        self,
        user_id: int,
        address_text: str,
        lat: float,
        lon: float,
        darkstore_id: str,
        is_active: bool = True,
    ) -> int:
        query = (
            insert(UserAddressModel)
            .values(
                user_id=user_id,
                address_text=address_text,
                lat=lat,
                lon=lon,
                darkstore_id=darkstore_id,
                is_active=is_active,
            )
            .returning(UserAddressModel.id)
        )

        return await self.session.scalar(query)

    async def deactivate_user_addresses(
        self,
        user_id: int,
    ) -> None:
        query = (
            update(UserAddressModel)
            .where(
                UserAddressModel.user_id == user_id,
                UserAddressModel.is_active.is_(True),
            )
            .values(is_active=False)
        )

        await self.session.execute(query)

    async def activate_user_address(
        self,
        user_id: int,
        address_id: int,
    ) -> None:
        query = (
            update(UserAddressModel)
            .where(
                UserAddressModel.id == address_id,
                UserAddressModel.user_id == user_id,
            )
            .values(is_active=True)
        )

        await self.session.execute(query)

    async def get_active_user_address(
        self,
        user_id: int,
    ) -> UserAddressData | None:
        query = select(UserAddressModel).where(
            UserAddressModel.user_id == user_id,
            UserAddressModel.is_active.is_(True),
        )

        resp = await self.session.scalars(query)
        address = resp.one_or_none()

        if address is None:
            return None

        return UserAddressData(
            id=address.id,
            user_id=address.user_id,
            address_text=address.address_text,
            lat=address.lat,
            lon=address.lon,
            darkstore_id=address.darkstore_id,
            is_active=address.is_active,
        )

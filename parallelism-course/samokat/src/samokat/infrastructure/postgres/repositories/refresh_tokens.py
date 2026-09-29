from datetime import UTC, datetime

from sqlalchemy import insert, select, update

from samokat.infrastructure.postgres.models import RefreshTokenModel
from samokat.infrastructure.postgres.repositories.base import BaseRepo
from samokat.security.dto import RefreshTokenData


class RefreshTokenRepo(BaseRepo):
    async def add_refresh_token(
        self,
        user_id: int,
        token_hash: str,
        expires_at: datetime,
    ) -> None:
        query = insert(RefreshTokenModel).values(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        await self.session.execute(query)

    async def get_active_refresh_token_by_hash(
        self,
        token_hash: str,
    ) -> RefreshTokenData | None:
        query = select(
            RefreshTokenModel.id,
            RefreshTokenModel.user_id,
            RefreshTokenModel.token_hash,
            RefreshTokenModel.expires_at,
        ).where(
            RefreshTokenModel.token_hash == token_hash,
            RefreshTokenModel.revoked_at.is_(None),
            RefreshTokenModel.expires_at > datetime.now(UTC),
        )

        resp = await self.session.execute(query)
        row = resp.one_or_none()

        if row is None:
            return None

        return RefreshTokenData(
            id=row.id,
            user_id=row.user_id,
            token_hash=row.token_hash,
            expires_at=row.expires_at,
        )

    async def revoke_refresh_token(
        self,
        refresh_token_id: int,
    ) -> None:
        query = (
            update(RefreshTokenModel)
            .where(
                RefreshTokenModel.id == refresh_token_id,
                RefreshTokenModel.revoked_at.is_(None),
            )
            .values(
                revoked_at=datetime.now(UTC),
            )
        )

        await self.session.execute(query)

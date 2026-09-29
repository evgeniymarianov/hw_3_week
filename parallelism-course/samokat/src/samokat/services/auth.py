from samokat.domain.exceptions import InvalidRefreshTokenError
from samokat.domain.exceptions import InvalidCredentialsError
from samokat.infrastructure.postgres.manager import DatabaseManager
from samokat.security.security_manager import SecurityManager
from samokat.application.dto import TokenPairData


class AuthService:
    def __init__(
        self,
        db: DatabaseManager,
        security: SecurityManager,
    ) -> None:
        self.db = db
        self.security = security

    async def register_new_user(self, username: str, plain_password: str):
        hashed_password = self.security.password_hasher.hash_password(plain_password)
        await self.db.users.add_user(
            username=username,
            hashed_password=hashed_password,
        )
        await self.db.commit()

    async def login_user(self, username: str, plain_password: str):
        user_auth_data = await self.db.users.get_user_hashed_password(username)
        if user_auth_data.hashed_password is None:
            raise InvalidCredentialsError

        is_valid_password = self.security.password_hasher.verify_password(
            user_auth_data.hashed_password,
            plain_password,
        )
        if not is_valid_password:
            raise InvalidCredentialsError

        new_tokens = await self._issue_token_pair(user_auth_data.user_id)

        await self.db.commit()

        return new_tokens

    async def refresh_token_pair(
        self,
        refresh_token: str,
    ) -> TokenPairData:
        refresh_token_hash = self.security.token_processor.hash_refresh_token(
            refresh_token
        )

        stored_refresh_token = (
            await self.db.refresh_tokens.get_active_refresh_token_by_hash(
                token_hash=refresh_token_hash,
            )
        )

        if stored_refresh_token is None:
            raise InvalidRefreshTokenError

        await self.db.refresh_tokens.revoke_refresh_token(
            refresh_token_id=stored_refresh_token.id,
        )

        token_pair = await self._issue_token_pair(
            user_id=stored_refresh_token.user_id,
        )

        await self.db.commit()

        return token_pair

    async def _issue_token_pair(
        self,
        user_id: int,
    ) -> TokenPairData:
        access_token = self.security.token_processor.create_access_token(
            user_id=user_id,
        )
        refresh_token = self.security.token_processor.create_refresh_token()

        await self.db.refresh_tokens.add_refresh_token(
            user_id=user_id,
            token_hash=refresh_token.token_hash,
            expires_at=refresh_token.expires_at,
        )

        return TokenPairData(
            access_token=access_token.token,
            refresh_token=refresh_token.token,
        )

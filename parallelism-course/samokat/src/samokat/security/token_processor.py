import hashlib
import hmac
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from typing import Any

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError


from samokat.config import TokenConfig
from samokat.security.dto import AccessTokenData, RefreshTokenData


class TokenProcessorError(Exception):
    pass


class AccessTokenExpiredError(TokenProcessorError):
    pass


class InvalidAccessTokenError(TokenProcessorError):
    pass


class TokenProcessor:
    def __init__(self, config: TokenConfig) -> None:
        self._secret_key = config.secret_key.get_secret_value()
        self._algorithm = config.algorithm
        self._access_token_expire_minutes = config.access_token_expire_minutes
        self._refresh_token_expire_days = config.refresh_token_expire_days

    def create_access_token(self, user_id: int) -> AccessTokenData:
        now = datetime.now(UTC)
        expires_at = now + timedelta(
            minutes=self._access_token_expire_minutes,
        )

        payload = {
            "sub": str(user_id),
            "iat": now,
            "exp": expires_at,
            "type": "access",
        }

        token = jwt.encode(
            payload=payload,
            key=self._secret_key,
            algorithm=self._algorithm,
        )

        return AccessTokenData(
            token=token,
            expires_at=expires_at,
        )

    def decode_access_token(self, token: str) -> dict[str, Any]:
        try:
            payload = jwt.decode(
                jwt=token,
                key=self._secret_key,
                algorithms=[self._algorithm],
            )
        except ExpiredSignatureError:
            raise AccessTokenExpiredError
        except InvalidTokenError:
            raise InvalidAccessTokenError

        if payload.get("type") != "access":
            raise InvalidAccessTokenError

        return payload

    def get_user_id_from_access_token(self, token: str) -> int:
        payload = self.decode_access_token(token)

        user_id = payload.get("sub")

        if user_id is None:
            raise InvalidAccessTokenError

        try:
            return int(user_id)
        except ValueError:
            raise InvalidAccessTokenError

    def create_refresh_token(self) -> RefreshTokenData:
        token = token_urlsafe(64)
        expires_at = datetime.now(UTC) + timedelta(
            days=self._refresh_token_expire_days,
        )

        return RefreshTokenData(
            token=token,
            token_hash=self.hash_refresh_token(token),
            expires_at=expires_at,
        )

    def hash_refresh_token(self, token: str) -> str:
        return hmac.new(
            key=self._secret_key.encode(),
            msg=token.encode(),
            digestmod=hashlib.sha256,
        ).hexdigest()

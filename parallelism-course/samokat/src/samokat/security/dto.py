from pydantic import BaseModel, ConfigDict
from datetime import datetime


class AccessTokenData(BaseModel):
    token: str
    expires_at: datetime

    model_config = ConfigDict(frozen=True)


class RefreshTokenData(BaseModel):
    id: int | None = None
    user_id: int | None = None
    token: str | None = None
    token_hash: str
    expires_at: datetime

    model_config = ConfigDict(frozen=True)

from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from samokat.security.security_manager import SecurityManager
from samokat.security.token_processor import (
    AccessTokenExpiredError,
    InvalidAccessTokenError,
)

bearer_scheme = HTTPBearer()


@inject
async def get_current_user_id(  # noqa: RUF029
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    security: FromDishka[SecurityManager],
) -> int:
    try:
        return security.token_processor.get_user_id_from_access_token(
            credentials.credentials,
        )
    except AccessTokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token expired",
        )
    except InvalidAccessTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )


UserIdDep = Annotated[int, Depends(get_current_user_id)]

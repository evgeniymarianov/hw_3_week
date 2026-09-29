from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from samokat.domain.exceptions import (
    CartIsEmptyError,
    DomainError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    OrderNotFoundError,
    ProductCardNotFoundError,
    UserAddressNotFoundError,
    UserNotFoundError,
)

DOMAIN_ERROR_RESPONSES: dict[type[DomainError], tuple[int, str]] = {
    InvalidRefreshTokenError: (
        status.HTTP_401_UNAUTHORIZED,
        "Invalid refresh token",
    ),
    InvalidCredentialsError: (
        status.HTTP_401_UNAUTHORIZED,
        "Invalid username or password",
    ),
    ProductCardNotFoundError: (
        status.HTTP_404_NOT_FOUND,
        "Product not found",
    ),
    UserAddressNotFoundError: (
        status.HTTP_404_NOT_FOUND,
        "User address not found",
    ),
    UserNotFoundError: (
        status.HTTP_404_NOT_FOUND,
        "User not found",
    ),
    CartIsEmptyError: (
        status.HTTP_400_BAD_REQUEST,
        "Cart is empty",
    ),
    OrderNotFoundError: (
        status.HTTP_404_NOT_FOUND,
        "Order not found",
    ),
}


def setup_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_exception_handler(  # noqa: RUF029
        _: Request,
        exc: DomainError,
    ) -> JSONResponse:
        status_code, message = _get_domain_error_response(exc)

        return JSONResponse(
            status_code=status_code,
            content={"detail": message},
        )


def _get_domain_error_response(exc: DomainError) -> tuple[int, str]:
    for error_type, response in DOMAIN_ERROR_RESPONSES.items():
        if isinstance(exc, error_type):
            return response

    return status.HTTP_400_BAD_REQUEST, "Unknown error"

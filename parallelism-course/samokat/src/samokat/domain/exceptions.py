class DomainError(Exception):
    pass


class AuthError(DomainError):
    pass


class InvalidRefreshTokenError(AuthError):
    pass


class InvalidCredentialsError(AuthError):
    pass


class InvalidPasswordError(AuthError):
    pass


class ProductError(DomainError):
    pass


class ProductCardNotFoundError(ProductError):
    pass


class AddressError(DomainError):
    pass


class UserAddressNotFoundError(AddressError):
    pass


class UserError(DomainError):
    pass


class UserNotFoundError(UserError):
    pass


class OrderError(DomainError):
    pass


class CartIsEmptyError(OrderError):
    pass


class OrderNotFoundError(OrderError):
    pass

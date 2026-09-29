from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from samokat.domain.exceptions import InvalidPasswordError


class PasswordHasherManager:
    def __init__(self, password_hasher: PasswordHasher):
        self.ph = password_hasher

    def hash_password(self, plain_password: str) -> str:
        return self.ph.hash(plain_password)

    def verify_password(self, hashed_password: str, plain_password: str) -> bool:
        try:
            return self.ph.verify(hashed_password, plain_password)
        except VerifyMismatchError:
            raise InvalidPasswordError

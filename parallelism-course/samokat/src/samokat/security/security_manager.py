from dataclasses import dataclass

from samokat.security.password_hasher import PasswordHasherManager
from samokat.security.token_processor import TokenProcessor


@dataclass(frozen=True, slots=True)
class SecurityManager:
    password_hasher: PasswordHasherManager
    token_processor: TokenProcessor

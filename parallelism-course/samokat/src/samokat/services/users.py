from samokat.domain.exceptions import UserNotFoundError
from samokat.infrastructure.postgres.manager import DatabaseManager


class UserService:
    def __init__(
        self,
        db: DatabaseManager,
    ) -> None:
        self.db = db

    async def get_user(self, user_id: int):
        user = await self.db.users.get_user(user_id)
        if not user:
            raise UserNotFoundError
        return user

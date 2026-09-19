from uuid import UUID

from app.modules.users.domain.entities import UserAccount
from app.modules.users.domain.exceptions import UserAccountInactiveError, UserNotFoundError
from app.modules.users.domain.repositories import UserAccountRepository


async def get_active_user(
    users: UserAccountRepository,
    user_id: UUID,
) -> UserAccount:
    user = await users.get_by_id(user_id)
    if user is None or user.deleted:
        raise UserNotFoundError
    if not user.is_active:
        raise UserAccountInactiveError
    return user

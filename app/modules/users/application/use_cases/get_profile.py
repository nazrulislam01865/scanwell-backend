from app.modules.users.application.dto import UserProfileDTO, to_profile_dto
from app.modules.users.application.queries import GetProfileQuery
from app.modules.users.application.use_cases._helpers import get_active_user
from app.modules.users.domain.repositories import UserAccountRepository


class GetProfile:
    def __init__(self, *, users: UserAccountRepository) -> None:
        self._users = users

    async def execute(self, query: GetProfileQuery) -> UserProfileDTO:
        user = await get_active_user(self._users, query.user_id)
        return to_profile_dto(user)

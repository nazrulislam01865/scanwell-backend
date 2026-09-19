from app.modules.users.application.dto import UserPreferencesDTO, to_preferences_dto
from app.modules.users.application.queries import GetPreferencesQuery
from app.modules.users.application.use_cases._helpers import get_active_user
from app.modules.users.domain.repositories import UserAccountRepository, UserPreferencesRepository


class GetPreferences:
    def __init__(
        self,
        *,
        users: UserAccountRepository,
        preferences: UserPreferencesRepository,
    ) -> None:
        self._users = users
        self._preferences = preferences

    async def execute(self, query: GetPreferencesQuery) -> UserPreferencesDTO:
        user = await get_active_user(self._users, query.user_id)
        preferences = await self._preferences.get_by_user_id(user.id)
        return to_preferences_dto(user, preferences)

from datetime import UTC, datetime

from app.modules.users.application.dto import (
    PersonalDataExportDTO,
    to_preferences_dto,
    to_profile_dto,
)
from app.modules.users.application.queries import ExportPersonalDataQuery
from app.modules.users.application.use_cases._helpers import get_active_user
from app.modules.users.domain.repositories import UserAccountRepository, UserPreferencesRepository


class ExportPersonalData:
    def __init__(
        self,
        *,
        users: UserAccountRepository,
        preferences: UserPreferencesRepository,
    ) -> None:
        self._users = users
        self._preferences = preferences

    async def execute(self, query: ExportPersonalDataQuery) -> PersonalDataExportDTO:
        user = await get_active_user(self._users, query.user_id)
        preferences = await self._preferences.get_by_user_id(user.id)
        return PersonalDataExportDTO(
            exported_at=datetime.now(UTC),
            profile=to_profile_dto(user),
            preferences=to_preferences_dto(user, preferences),
        )

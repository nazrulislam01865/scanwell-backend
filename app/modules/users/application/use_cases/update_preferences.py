from datetime import UTC, datetime

from app.core.database.transaction import TransactionManager
from app.modules.users.application.commands import UpdatePreferencesCommand
from app.modules.users.application.dto import UserPreferencesDTO, to_preferences_dto
from app.modules.users.application.use_cases._helpers import get_active_user
from app.modules.users.domain.entities import UserPreferences
from app.modules.users.domain.repositories import UserAccountRepository, UserPreferencesRepository


class UpdatePreferences:
    def __init__(
        self,
        *,
        users: UserAccountRepository,
        preferences: UserPreferencesRepository,
        transaction: TransactionManager,
    ) -> None:
        self._users = users
        self._preferences = preferences
        self._transaction = transaction

    async def execute(self, command: UpdatePreferencesCommand) -> UserPreferencesDTO:
        user = await get_active_user(self._users, command.user_id)
        now = datetime.now(UTC)

        preferences = await self._preferences.get_by_user_id(user.id)
        if preferences is None:
            preferences = UserPreferences(
                user_id=user.id,
                email_notifications=(
                    command.email_notifications
                    if command.email_notifications is not None
                    else True
                ),
                push_notifications=(
                    command.push_notifications
                    if command.push_notifications is not None
                    else True
                ),
                created_at=now,
                updated_at=now,
            )
            await self._preferences.add(preferences)
        else:
            preferences.update(
                email_notifications=command.email_notifications,
                push_notifications=command.push_notifications,
                when=now,
            )
            await self._preferences.save(preferences)

        if command.preferred_login_method is not None:
            user.update_preferred_login_method(
                command.preferred_login_method,
                when=now,
            )
            await self._users.save(user)

        await self._transaction.commit()
        return to_preferences_dto(user, preferences)

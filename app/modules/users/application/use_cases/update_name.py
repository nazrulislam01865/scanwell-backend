from datetime import UTC, datetime

from app.core.database.transaction import TransactionManager
from app.modules.users.application.commands import UpdateNameCommand
from app.modules.users.application.dto import UserProfileDTO, to_profile_dto
from app.modules.users.application.use_cases._helpers import get_active_user
from app.modules.users.domain.repositories import UserAccountRepository


class UpdateName:
    def __init__(
        self,
        *,
        users: UserAccountRepository,
        transaction: TransactionManager,
    ) -> None:
        self._users = users
        self._transaction = transaction

    async def execute(self, command: UpdateNameCommand) -> UserProfileDTO:
        user = await get_active_user(self._users, command.user_id)
        user.update_name(command.name, when=datetime.now(UTC))
        await self._users.save(user)
        await self._transaction.commit()
        return to_profile_dto(user)

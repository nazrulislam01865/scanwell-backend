import secrets
from datetime import UTC, datetime

from app.core.database.transaction import TransactionManager
from app.core.security.passwords import hash_password, verify_password
from app.modules.users.application.commands import DeleteAccountCommand
from app.modules.users.application.use_cases._helpers import get_active_user
from app.modules.users.domain.exceptions import InvalidAccountPasswordError
from app.modules.users.domain.repositories import (
    UserAccountRepository,
    UserPreferencesRepository,
    UserSecurityRepository,
)


class DeleteAccount:
    def __init__(
        self,
        *,
        users: UserAccountRepository,
        preferences: UserPreferencesRepository,
        security: UserSecurityRepository,
        transaction: TransactionManager,
    ) -> None:
        self._users = users
        self._preferences = preferences
        self._security = security
        self._transaction = transaction

    async def execute(self, command: DeleteAccountCommand) -> None:
        user = await get_active_user(self._users, command.user_id)
        if not verify_password(command.password, user.password_hash):
            raise InvalidAccountPasswordError

        now = datetime.now(UTC)
        replacement_password_hash = hash_password(secrets.token_urlsafe(32))
        user.mark_deleted(
            replacement_password_hash=replacement_password_hash,
            when=now,
        )

        await self._users.save(user)
        await self._preferences.delete_for_user(user.id)
        await self._security.revoke_all_sessions(
            user.id,
            revoked_at=now,
            reason="account_deleted",
        )
        await self._security.invalidate_all_verification_codes(
            user.id,
            consumed_at=now,
        )
        await self._transaction.commit()

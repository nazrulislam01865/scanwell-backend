from datetime import UTC, datetime

from app.core.database.transaction import TransactionManager
from app.modules.auth.application.commands import LogoutAllCommand
from app.modules.auth.domain.repositories import AuthSessionRepository


class LogoutAll:
    def __init__(
        self,
        *,
        sessions: AuthSessionRepository,
        transaction: TransactionManager,
    ) -> None:
        self._sessions = sessions
        self._transaction = transaction

    async def execute(self, command: LogoutAllCommand) -> None:
        await self._sessions.revoke_all_for_user(
            command.user_id,
            revoked_at=datetime.now(UTC),
            reason="logout_all",
        )
        await self._transaction.commit()

from app.core.database.transaction import TransactionManager
from app.modules.auth.application.commands import LogoutUserCommand
from app.modules.auth.application.session_service import AuthSessionService


class LogoutUser:
    def __init__(
        self,
        *,
        sessions: AuthSessionService,
        transaction: TransactionManager,
    ) -> None:
        self._sessions = sessions
        self._transaction = transaction

    async def execute(self, command: LogoutUserCommand) -> None:
        await self._sessions.revoke(
            refresh_token=command.refresh_token,
            reason="logout",
        )
        await self._transaction.commit()

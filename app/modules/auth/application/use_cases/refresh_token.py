from app.core.database.transaction import TransactionManager
from app.modules.auth.application.commands import RefreshTokenCommand
from app.modules.auth.application.session_service import AuthSessionService
from app.modules.auth.domain.exceptions import AccountDisabledError, InvalidAuthTokenError
from app.modules.auth.domain.repositories import UserRepository
from app.modules.auth.domain.value_objects import AuthTokens


class RefreshToken:
    def __init__(
        self,
        *,
        users: UserRepository,
        sessions: AuthSessionService,
        transaction: TransactionManager,
    ) -> None:
        self._users = users
        self._sessions = sessions
        self._transaction = transaction

    async def execute(self, command: RefreshTokenCommand) -> AuthTokens:
        user_id, tokens = await self._sessions.rotate(
            refresh_token=command.refresh_token
        )
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise InvalidAuthTokenError
        if not user.is_active:
            raise AccountDisabledError

        await self._transaction.commit()
        return tokens

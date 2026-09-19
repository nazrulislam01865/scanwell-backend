from app.core.database.transaction import TransactionManager
from app.core.security.passwords import verify_password
from app.modules.auth.application.commands import LoginUserCommand
from app.modules.auth.application.dto import AuthResult, to_user_dto
from app.modules.auth.application.session_service import AuthSessionService
from app.modules.auth.domain.exceptions import (
    AccountDisabledError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
)
from app.modules.auth.domain.repositories import UserRepository
from app.modules.auth.domain.value_objects import normalize_email


class LoginUser:
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

    async def execute(self, command: LoginUserCommand) -> AuthResult:
        user = await self._users.get_by_email(normalize_email(command.email))
        if user is None or not verify_password(command.password, user.password_hash):
            raise InvalidCredentialsError
        if not user.is_active:
            raise AccountDisabledError
        if not user.email_verified:
            raise EmailNotVerifiedError

        tokens = await self._sessions.issue(user_id=user.id)
        await self._transaction.commit()

        return AuthResult(
            user=to_user_dto(user),
            tokens=tokens,
        )

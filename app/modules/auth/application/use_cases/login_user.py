from app.core.security.passwords import verify_password
from app.modules.auth.application.commands import LoginUserCommand
from app.modules.auth.application.dto import AuthResult, to_user_dto
from app.modules.auth.domain.exceptions import (
    AccountDisabledError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
)
from app.modules.auth.domain.repositories import TokenService, UserRepository
from app.modules.auth.domain.value_objects import normalize_email


class LoginUser:
    def __init__(self, *, users: UserRepository, token_service: TokenService) -> None:
        self._users = users
        self._token_service = token_service

    async def execute(self, command: LoginUserCommand) -> AuthResult:
        user = await self._users.get_by_email(normalize_email(command.email))
        if user is None or not verify_password(command.password, user.password_hash):
            raise InvalidCredentialsError
        if not user.is_active:
            raise AccountDisabledError
        if not user.email_verified:
            raise EmailNotVerifiedError
        return AuthResult(
            user=to_user_dto(user),
            tokens=self._token_service.issue_pair(user_id=user.id),
        )

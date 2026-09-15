from app.modules.auth.application.commands import RefreshTokenCommand
from app.modules.auth.domain.exceptions import AccountDisabledError, InvalidAuthTokenError
from app.modules.auth.domain.repositories import TokenService, UserRepository
from app.modules.auth.domain.value_objects import AuthTokens


class RefreshToken:
    def __init__(self, *, users: UserRepository, token_service: TokenService) -> None:
        self._users = users
        self._token_service = token_service

    async def execute(self, command: RefreshTokenCommand) -> AuthTokens:
        try:
            user_id = self._token_service.subject_from_refresh(command.refresh_token)
        except (ValueError, TypeError) as exc:
            raise InvalidAuthTokenError from exc
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise InvalidAuthTokenError
        if not user.is_active:
            raise AccountDisabledError
        return self._token_service.issue_pair(user_id=user.id)

from app.modules.auth.application.dto import AuthUserDTO, to_user_dto
from app.modules.auth.application.queries import CurrentUserQuery
from app.modules.auth.domain.exceptions import AccountDisabledError, AuthUserNotFoundError
from app.modules.auth.domain.repositories import UserRepository


class GetCurrentUser:
    def __init__(self, *, users: UserRepository) -> None:
        self._users = users

    async def execute(self, query: CurrentUserQuery) -> AuthUserDTO:
        user = await self._users.get_by_id(query.user_id)
        if user is None:
            raise AuthUserNotFoundError
        if not user.is_active:
            raise AccountDisabledError
        return to_user_dto(user)

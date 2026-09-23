from datetime import UTC, datetime

from app.modules.auth.application.admin_dto import AdminDTO, to_admin_dto
from app.modules.auth.domain.admin_repositories import AdminRepository
from app.modules.auth.domain.exceptions import AccountDisabledError, InvalidAuthTokenError
from app.modules.auth.domain.repositories import AuthSessionRepository, TokenService


class GetCurrentAdmin:
    def __init__(
        self,
        *,
        admins: AdminRepository,
        sessions: AuthSessionRepository,
        token_service: TokenService,
    ) -> None:
        self._admins = admins
        self._sessions = sessions
        self._token_service = token_service

    async def execute(self, access_token: str) -> AdminDTO:
        identity = self._token_service.access_identity(access_token)
        session = await self._sessions.get_by_id(identity.session_id)
        now = datetime.now(UTC)

        if session is None or session.user_id != identity.user_id:
            raise InvalidAuthTokenError
        if session.revoked or session.is_expired(now=now):
            raise InvalidAuthTokenError

        admin = await self._admins.get_by_id(identity.user_id)
        if admin is None:
            raise InvalidAuthTokenError
        if not admin.is_active:
            raise AccountDisabledError

        return to_admin_dto(admin)

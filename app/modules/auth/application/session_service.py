from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.modules.auth.domain.entities import AuthSession
from app.modules.auth.domain.exceptions import AuthSessionRevokedError, InvalidAuthTokenError
from app.modules.auth.domain.repositories import AuthSessionRepository, TokenService
from app.modules.auth.domain.value_objects import AuthTokens


class AuthSessionService:
    """Creates, validates, rotates, and revokes persisted refresh sessions.

    This service deliberately does not commit transactions. The calling use case
    owns the transaction boundary so user/code/session changes can be committed
    atomically.
    """

    def __init__(
        self,
        *,
        sessions: AuthSessionRepository,
        token_service: TokenService,
    ) -> None:
        self._sessions = sessions
        self._token_service = token_service

    async def issue(self, *, user_id: UUID, now: datetime | None = None) -> AuthTokens:
        issued_at = now or datetime.now(UTC)
        session_id = uuid4()
        tokens = self._token_service.issue_pair(
            user_id=user_id,
            session_id=session_id,
        )
        identity = self._token_service.refresh_identity(tokens.refresh_token)
        await self._sessions.add(
            AuthSession(
                id=session_id,
                user_id=user_id,
                refresh_token_hash=self._token_service.hash_refresh_token(
                    tokens.refresh_token
                ),
                expires_at=identity.expires_at,
                created_at=issued_at,
                last_used_at=issued_at,
            )
        )
        return tokens

    async def rotate(
        self,
        *,
        refresh_token: str,
        now: datetime | None = None,
    ) -> tuple[UUID, AuthTokens]:
        current_time = now or datetime.now(UTC)
        identity = self._token_service.refresh_identity(refresh_token)
        session = await self._sessions.get_by_id(identity.session_id)

        if session is None or session.user_id != identity.user_id:
            raise InvalidAuthTokenError
        if session.revoked:
            raise AuthSessionRevokedError
        if session.is_expired(now=current_time):
            raise InvalidAuthTokenError
        if not self._token_service.refresh_token_matches(
            refresh_token,
            session.refresh_token_hash,
        ):
            raise InvalidAuthTokenError

        tokens = self._token_service.issue_pair(
            user_id=session.user_id,
            session_id=session.id,
        )
        new_identity = self._token_service.refresh_identity(tokens.refresh_token)
        session.rotate(
            refresh_token_hash=self._token_service.hash_refresh_token(
                tokens.refresh_token
            ),
            expires_at=new_identity.expires_at,
            when=current_time,
        )
        await self._sessions.save(session)
        return session.user_id, tokens

    async def revoke(
        self,
        *,
        refresh_token: str,
        now: datetime | None = None,
        reason: str = "logout",
    ) -> None:
        current_time = now or datetime.now(UTC)
        identity = self._token_service.refresh_identity(refresh_token)
        session = await self._sessions.get_by_id(identity.session_id)

        if session is None or session.user_id != identity.user_id:
            raise InvalidAuthTokenError
        if not self._token_service.refresh_token_matches(
            refresh_token,
            session.refresh_token_hash,
        ):
            raise InvalidAuthTokenError

        session.revoke(when=current_time, reason=reason)
        await self._sessions.save(session)

import hashlib
import hmac
from uuid import UUID

from app.core.security.jwt import InvalidTokenError, JWTService
from app.modules.auth.domain.exceptions import InvalidAuthTokenError
from app.modules.auth.domain.value_objects import (
    AccessTokenIdentity,
    AuthTokens,
    RefreshTokenIdentity,
)


class AuthTokenService:
    def __init__(self, *, jwt_service: JWTService, access_expires_in: int) -> None:
        self._jwt_service = jwt_service
        self._access_expires_in = access_expires_in

    def issue_pair(self, *, user_id: UUID, session_id: UUID) -> AuthTokens:
        return AuthTokens(
            access_token=self._jwt_service.create_access_token(
                user_id=user_id,
                session_id=session_id,
            ),
            refresh_token=self._jwt_service.create_refresh_token(
                user_id=user_id,
                session_id=session_id,
            ),
            expires_in=self._access_expires_in,
        )

    def subject_from_access(self, token: str) -> UUID:
        try:
            return self._jwt_service.decode(token, expected_type="access").subject
        except InvalidTokenError as exc:
            raise InvalidAuthTokenError from exc

    def access_identity(self, token: str) -> AccessTokenIdentity:
        try:
            claims = self._jwt_service.decode(token, expected_type="access")
        except InvalidTokenError as exc:
            raise InvalidAuthTokenError from exc

        if claims.session_id is None:
            raise InvalidAuthTokenError

        return AccessTokenIdentity(
            user_id=claims.subject,
            session_id=claims.session_id,
            expires_at=claims.expires_at,
        )

    def refresh_identity(self, token: str) -> RefreshTokenIdentity:
        try:
            claims = self._jwt_service.decode(token, expected_type="refresh")
        except InvalidTokenError as exc:
            raise InvalidAuthTokenError from exc

        if claims.session_id is None:
            raise InvalidAuthTokenError

        return RefreshTokenIdentity(
            user_id=claims.subject,
            session_id=claims.session_id,
            expires_at=claims.expires_at,
        )

    def hash_refresh_token(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def refresh_token_matches(self, token: str, expected_hash: str) -> bool:
        actual_hash = self.hash_refresh_token(token)
        return hmac.compare_digest(actual_hash, expected_hash)

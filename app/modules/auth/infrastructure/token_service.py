from uuid import UUID

from app.core.security.jwt import InvalidTokenError, JWTService
from app.modules.auth.domain.exceptions import InvalidAuthTokenError
from app.modules.auth.domain.value_objects import AuthTokens


class AuthTokenService:
    def __init__(self, *, jwt_service: JWTService, access_expires_in: int) -> None:
        self._jwt_service = jwt_service
        self._access_expires_in = access_expires_in

    def issue_pair(self, *, user_id: UUID) -> AuthTokens:
        return AuthTokens(
            access_token=self._jwt_service.create_access_token(user_id=user_id),
            refresh_token=self._jwt_service.create_refresh_token(user_id=user_id),
            expires_in=self._access_expires_in,
        )

    def subject_from_access(self, token: str) -> UUID:
        try:
            return self._jwt_service.decode(token, expected_type="access").subject
        except InvalidTokenError as exc:
            raise InvalidAuthTokenError from exc

    def subject_from_refresh(self, token: str) -> UUID:
        try:
            return self._jwt_service.decode(token, expected_type="refresh").subject
        except InvalidTokenError as exc:
            raise InvalidAuthTokenError from exc

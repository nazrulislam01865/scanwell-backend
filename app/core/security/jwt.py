from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID, uuid4

import jwt
from jwt import InvalidTokenError as PyJWTInvalidTokenError

TokenType = Literal["access", "refresh"]


class InvalidTokenError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class TokenClaims:
    subject: UUID
    token_type: TokenType
    jti: str
    issued_at: datetime
    expires_at: datetime
    session_id: UUID | None = None


class JWTService:
    def __init__(
        self,
        *,
        secret_key: str,
        algorithm: str,
        issuer: str,
        audience: str,
        access_token_ttl: timedelta,
        refresh_token_ttl: timedelta,
    ) -> None:
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._issuer = issuer
        self._audience = audience
        self._access_token_ttl = access_token_ttl
        self._refresh_token_ttl = refresh_token_ttl

    def create_access_token(self, *, user_id: UUID, session_id: UUID | None = None) -> str:
        return self._create_token(
            user_id=user_id,
            token_type="access",
            session_id=session_id,
        )

    def create_refresh_token(self, *, user_id: UUID, session_id: UUID | None = None) -> str:
        return self._create_token(
            user_id=user_id,
            token_type="refresh",
            session_id=session_id,
        )

    def decode(self, token: str, *, expected_type: TokenType) -> TokenClaims:
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
                issuer=self._issuer,
                audience=self._audience,
                options={"require": ["sub", "type", "jti", "iat", "exp", "iss", "aud"]},
            )
            token_type = payload["type"]
            if token_type != expected_type:
                raise InvalidTokenError("Unexpected token type")

            raw_session_id = payload.get("sid")
            session_id = UUID(raw_session_id) if raw_session_id is not None else None

            return TokenClaims(
                subject=UUID(payload["sub"]),
                token_type=token_type,
                jti=str(payload["jti"]),
                issued_at=datetime.fromtimestamp(payload["iat"], tz=UTC),
                expires_at=datetime.fromtimestamp(payload["exp"], tz=UTC),
                session_id=session_id,
            )
        except (PyJWTInvalidTokenError, KeyError, TypeError, ValueError) as exc:
            if isinstance(exc, InvalidTokenError):
                raise
            raise InvalidTokenError("Invalid or expired token") from exc

    def _create_token(
        self,
        *,
        user_id: UUID,
        token_type: TokenType,
        session_id: UUID | None,
    ) -> str:
        now = datetime.now(UTC)
        ttl = self._access_token_ttl if token_type == "access" else self._refresh_token_ttl
        payload = {
            "sub": str(user_id),
            "type": token_type,
            "jti": str(uuid4()),
            "iat": now,
            "exp": now + ttl,
            "iss": self._issuer,
            "aud": self._audience,
        }
        if session_id is not None:
            payload["sid"] = str(session_id)
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

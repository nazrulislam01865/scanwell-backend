import hashlib
import hmac
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.modules.auth.domain.entities import AuthSession, AuthUser, VerificationCode
from app.modules.auth.domain.repositories import EmailService, TokenService
from app.modules.auth.domain.value_objects import (
    AuthTokens,
    RefreshTokenIdentity,
    VerificationPurpose,
)


class InMemoryUserRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, AuthUser] = {}
        self.saved_ids: list[UUID] = []

    async def get_by_email(self, email: str) -> AuthUser | None:
        return next((user for user in self.items.values() if user.email == email), None)

    async def get_by_id(self, user_id: UUID) -> AuthUser | None:
        return self.items.get(user_id)

    async def add(self, user: AuthUser) -> None:
        self.items[user.id] = user

    async def save(self, user: AuthUser) -> None:
        self.items[user.id] = user
        self.saved_ids.append(user.id)


class InMemoryVerificationCodeRepository:
    def __init__(self) -> None:
        self.items: list[VerificationCode] = []
        self.saved_ids: list[UUID] = []

    async def add(self, code: VerificationCode) -> None:
        self.items.append(code)

    async def save(self, code: VerificationCode) -> None:
        self.saved_ids.append(code.id)

    async def get_latest_active(
        self,
        user_id: UUID,
        purpose: VerificationPurpose,
    ) -> VerificationCode | None:
        matches = [
            code
            for code in self.items
            if code.user_id == user_id
            and code.purpose == purpose
            and code.consumed_at is None
        ]
        return max(matches, key=lambda item: item.created_at, default=None)

    async def invalidate_active(
        self,
        user_id: UUID,
        purpose: VerificationPurpose,
        consumed_at: datetime,
    ) -> None:
        for code in self.items:
            if (
                code.user_id == user_id
                and code.purpose == purpose
                and code.consumed_at is None
            ):
                code.consumed_at = consumed_at


class InMemoryAuthSessionRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, AuthSession] = {}
        self.saved_ids: list[UUID] = []

    async def add(self, session: AuthSession) -> None:
        self.items[session.id] = session

    async def save(self, session: AuthSession) -> None:
        self.items[session.id] = session
        self.saved_ids.append(session.id)

    async def get_by_id(self, session_id: UUID) -> AuthSession | None:
        return self.items.get(session_id)

    async def revoke_all_for_user(
        self,
        user_id: UUID,
        *,
        revoked_at: datetime,
        reason: str,
    ) -> None:
        for session in self.items.values():
            if session.user_id == user_id and not session.revoked:
                session.revoke(when=revoked_at, reason=reason)
                self.saved_ids.append(session.id)


class FakeTransaction:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1


class FakeEmailService(EmailService):
    def __init__(self) -> None:
        self.sent: list[tuple[str, str, VerificationPurpose]] = []

    async def send_verification_code(
        self,
        *,
        email: str,
        code: str,
        purpose: VerificationPurpose,
    ) -> None:
        self.sent.append((email, code, purpose))


class FakeTokenService(TokenService):
    def __init__(self) -> None:
        self._counter = 0

    def issue_pair(self, *, user_id: UUID, session_id: UUID) -> AuthTokens:
        self._counter += 1
        suffix = str(self._counter)
        return AuthTokens(
            access_token=f"access:{user_id}:{session_id}:{suffix}",
            refresh_token=f"refresh:{user_id}:{session_id}:{suffix}",
            expires_in=900,
        )

    def subject_from_access(self, token: str) -> UUID:
        parts = token.split(":")
        if len(parts) < 2 or parts[0] != "access":
            raise ValueError("invalid access token")
        return UUID(parts[1])

    def refresh_identity(self, token: str) -> RefreshTokenIdentity:
        parts = token.split(":")
        if len(parts) != 4 or parts[0] != "refresh":
            raise ValueError("invalid refresh token")
        return RefreshTokenIdentity(
            user_id=UUID(parts[1]),
            session_id=UUID(parts[2]),
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )

    def hash_refresh_token(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def refresh_token_matches(self, token: str, expected_hash: str) -> bool:
        return hmac.compare_digest(self.hash_refresh_token(token), expected_hash)


def utcnow() -> datetime:
    return datetime.now(UTC)

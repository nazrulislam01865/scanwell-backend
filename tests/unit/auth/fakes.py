from datetime import UTC, datetime
from uuid import UUID

from app.modules.auth.domain.entities import AuthUser, VerificationCode
from app.modules.auth.domain.repositories import EmailService, TokenService
from app.modules.auth.domain.value_objects import AuthTokens, VerificationPurpose


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
    def issue_pair(self, *, user_id: UUID) -> AuthTokens:
        return AuthTokens(
            access_token=f"access:{user_id}",
            refresh_token=f"refresh:{user_id}",
            expires_in=900,
        )

    def subject_from_access(self, token: str) -> UUID:
        prefix, value = token.split(":", 1)
        if prefix != "access":
            raise ValueError("invalid access token")
        return UUID(value)

    def subject_from_refresh(self, token: str) -> UUID:
        prefix, value = token.split(":", 1)
        if prefix != "refresh":
            raise ValueError("invalid refresh token")
        return UUID(value)


def utcnow() -> datetime:
    return datetime.now(UTC)

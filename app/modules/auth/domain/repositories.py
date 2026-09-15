from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.modules.auth.domain.entities import AuthUser, VerificationCode
from app.modules.auth.domain.value_objects import AuthTokens, VerificationPurpose


class UserRepository(Protocol):
    async def get_by_email(self, email: str) -> AuthUser | None: ...

    async def get_by_id(self, user_id: UUID) -> AuthUser | None: ...

    async def add(self, user: AuthUser) -> None: ...

    async def save(self, user: AuthUser) -> None: ...


class VerificationCodeRepository(Protocol):
    async def add(self, code: VerificationCode) -> None: ...

    async def save(self, code: VerificationCode) -> None: ...

    async def get_latest_active(
        self,
        user_id: UUID,
        purpose: VerificationPurpose,
    ) -> VerificationCode | None: ...

    async def invalidate_active(
        self,
        user_id: UUID,
        purpose: VerificationPurpose,
        consumed_at: datetime,
    ) -> None: ...


class EmailService(Protocol):
    async def send_verification_code(
        self,
        *,
        email: str,
        code: str,
        purpose: VerificationPurpose,
    ) -> None: ...


class TokenService(Protocol):
    def issue_pair(self, *, user_id: UUID) -> AuthTokens: ...

    def subject_from_access(self, token: str) -> UUID: ...

    def subject_from_refresh(self, token: str) -> UUID: ...

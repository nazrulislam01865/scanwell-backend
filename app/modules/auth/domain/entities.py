from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from app.modules.auth.domain.value_objects import LoginMethod, VerificationPurpose


@dataclass(slots=True)
class AuthUser:
    id: UUID
    name: str
    email: str
    phone: str | None
    password_hash: str
    preferred_login_method: LoginMethod
    email_verified_at: datetime | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @property
    def email_verified(self) -> bool:
        return self.email_verified_at is not None

    def mark_email_verified(self, *, when: datetime | None = None) -> None:
        now = when or datetime.now(UTC)
        self.email_verified_at = now
        self.updated_at = now


@dataclass(slots=True)
class VerificationCode:
    id: UUID
    user_id: UUID
    purpose: VerificationPurpose
    code_hash: str
    expires_at: datetime
    consumed_at: datetime | None
    failed_attempts: int
    created_at: datetime

    def is_expired(self, *, now: datetime | None = None) -> bool:
        return self.expires_at <= (now or datetime.now(UTC))

    def consume(self, *, when: datetime | None = None) -> None:
        self.consumed_at = when or datetime.now(UTC)

    def record_failed_attempt(self) -> None:
        self.failed_attempts += 1

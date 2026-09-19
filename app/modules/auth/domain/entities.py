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
    deleted_at: datetime | None = None

    @property
    def email_verified(self) -> bool:
        return self.email_verified_at is not None

    def mark_email_verified(self, *, when: datetime | None = None) -> None:
        now = when or datetime.now(UTC)
        self.email_verified_at = now
        self.updated_at = now

    def change_password_hash(
        self,
        password_hash: str,
        *,
        when: datetime | None = None,
    ) -> None:
        self.password_hash = password_hash
        self.updated_at = when or datetime.now(UTC)
        

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

@dataclass(slots=True)
class AuthSession:
    id: UUID
    user_id: UUID
    refresh_token_hash: str
    expires_at: datetime
    created_at: datetime
    last_used_at: datetime
    revoked_at: datetime | None = None
    revoked_reason: str | None = None

    @property
    def revoked(self) -> bool:
        return self.revoked_at is not None

    def is_expired(self, *, now: datetime | None = None) -> bool:
        return self.expires_at <= (now or datetime.now(UTC))

    def rotate(
        self,
        *,
        refresh_token_hash: str,
        expires_at: datetime,
        when: datetime | None = None,
    ) -> None:
        now = when or datetime.now(UTC)
        self.refresh_token_hash = refresh_token_hash
        self.expires_at = expires_at
        self.last_used_at = now

    def revoke(
        self,
        *,
        when: datetime | None = None,
        reason: str | None = None,
    ) -> None:
        if self.revoked_at is not None:
            return
        self.revoked_at = when or datetime.now(UTC)
        self.revoked_reason = reason


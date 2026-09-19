from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID


@dataclass(slots=True)
class UserAccount:
    id: UUID
    name: str
    email: str
    phone: str | None
    password_hash: str
    preferred_login_method: str
    email_verified_at: datetime | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    @property
    def email_verified(self) -> bool:
        return self.email_verified_at is not None

    @property
    def deleted(self) -> bool:
        return self.deleted_at is not None

    def update_name(self, name: str, *, when: datetime | None = None) -> None:
        self.name = name.strip()
        self.updated_at = when or datetime.now(UTC)

    def update_phone(self, phone: str | None, *, when: datetime | None = None) -> None:
        self.phone = (phone or "").strip() or None
        self.updated_at = when or datetime.now(UTC)

    def update_preferred_login_method(
        self,
        preferred_login_method: str,
        *,
        when: datetime | None = None,
    ) -> None:
        self.preferred_login_method = preferred_login_method
        self.updated_at = when or datetime.now(UTC)

    def mark_deleted(
        self,
        *,
        replacement_password_hash: str,
        when: datetime | None = None,
    ) -> None:
        now = when or datetime.now(UTC)
        self.name = "Deleted User"
        self.email = f"deleted+{self.id}@deleted.scanwell.invalid"
        self.phone = None
        self.password_hash = replacement_password_hash
        self.is_active = False
        self.deleted_at = now
        self.updated_at = now


@dataclass(slots=True)
class UserPreferences:
    user_id: UUID
    email_notifications: bool
    push_notifications: bool
    created_at: datetime
    updated_at: datetime

    def update(
        self,
        *,
        email_notifications: bool | None = None,
        push_notifications: bool | None = None,
        when: datetime | None = None,
    ) -> None:
        if email_notifications is not None:
            self.email_notifications = email_notifications
        if push_notifications is not None:
            self.push_notifications = push_notifications
        self.updated_at = when or datetime.now(UTC)

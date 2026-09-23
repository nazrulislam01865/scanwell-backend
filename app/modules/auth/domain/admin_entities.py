from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID


@dataclass(slots=True)
class Admin:
    id: UUID
    name: str
    email: str
    password_hash: str
    role: str
    status: str
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @property
    def is_active(self) -> bool:
        return self.status.strip().lower() == "active"

    def mark_logged_in(self, *, when: datetime | None = None) -> None:
        now = when or datetime.now(UTC)
        self.last_login_at = now
        self.updated_at = now

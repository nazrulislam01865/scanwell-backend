from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class UpdateProfileCommand:
    user_id: UUID
    name: str | None = None
    phone: str | None = None
    update_phone: bool = False


@dataclass(frozen=True, slots=True)
class UpdateNameCommand:
    user_id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class UpdatePhoneCommand:
    user_id: UUID
    phone: str | None


@dataclass(frozen=True, slots=True)
class UpdatePreferencesCommand:
    user_id: UUID
    email_notifications: bool | None = None
    push_notifications: bool | None = None
    preferred_login_method: str | None = None


@dataclass(frozen=True, slots=True)
class DeleteAccountCommand:
    user_id: UUID
    password: str

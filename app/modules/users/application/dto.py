from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.users.domain.entities import UserAccount, UserPreferences


@dataclass(frozen=True, slots=True)
class UserProfileDTO:
    id: UUID
    name: str
    email: str
    phone: str | None
    preferred_login_method: str
    email_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class UserPreferencesDTO:
    email_notifications: bool
    push_notifications: bool
    preferred_login_method: str


@dataclass(frozen=True, slots=True)
class PersonalDataExportDTO:
    exported_at: datetime
    profile: UserProfileDTO
    preferences: UserPreferencesDTO


def to_profile_dto(user: UserAccount) -> UserProfileDTO:
    return UserProfileDTO(
        id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        preferred_login_method=user.preferred_login_method,
        email_verified=user.email_verified,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def to_preferences_dto(
    user: UserAccount,
    preferences: UserPreferences | None,
) -> UserPreferencesDTO:
    return UserPreferencesDTO(
        email_notifications=(
            preferences.email_notifications if preferences is not None else True
        ),
        push_notifications=(
            preferences.push_notifications if preferences is not None else True
        ),
        preferred_login_method=user.preferred_login_method,
    )

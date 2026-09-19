from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.modules.auth.domain.value_objects import LoginMethod
from app.modules.users.application.dto import (
    PersonalDataExportDTO,
    UserPreferencesDTO,
    UserProfileDTO,
)


class UserProfileResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    phone: str | None
    preferred_login_method: LoginMethod
    email_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_dto(cls, profile: UserProfileDTO) -> "UserProfileResponse":
        return cls(
            id=profile.id,
            name=profile.name,
            email=profile.email,
            phone=profile.phone,
            preferred_login_method=LoginMethod(profile.preferred_login_method),
            email_verified=profile.email_verified,
            is_active=profile.is_active,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )


class UpdateProfileRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    phone: str | None = Field(default=None, max_length=40)

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> "UpdateProfileRequest":
        if not self.model_fields_set.intersection({"name", "phone"}):
            raise ValueError("At least one profile field must be provided.")
        return self


class UpdateNameRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)


class UpdatePhoneRequest(BaseModel):
    phone: str | None = Field(default=None, max_length=40)


class UserPreferencesResponse(BaseModel):
    email_notifications: bool
    push_notifications: bool
    preferred_login_method: LoginMethod

    @classmethod
    def from_dto(cls, preferences: UserPreferencesDTO) -> "UserPreferencesResponse":
        return cls(
            email_notifications=preferences.email_notifications,
            push_notifications=preferences.push_notifications,
            preferred_login_method=LoginMethod(preferences.preferred_login_method),
        )


class UpdatePreferencesRequest(BaseModel):
    email_notifications: bool | None = None
    push_notifications: bool | None = None
    preferred_login_method: LoginMethod | None = None

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> "UpdatePreferencesRequest":
        if not self.model_fields_set.intersection(
            {"email_notifications", "push_notifications", "preferred_login_method"}
        ):
            raise ValueError("At least one preference must be provided.")
        return self


class DeleteAccountRequest(BaseModel):
    password: str = Field(min_length=6, max_length=128)


class MessageResponse(BaseModel):
    message: str


class PersonalDataExportResponse(BaseModel):
    exported_at: datetime
    profile: UserProfileResponse
    preferences: UserPreferencesResponse

    @classmethod
    def from_dto(cls, data: PersonalDataExportDTO) -> "PersonalDataExportResponse":
        return cls(
            exported_at=data.exported_at,
            profile=UserProfileResponse.from_dto(data.profile),
            preferences=UserPreferencesResponse.from_dto(data.preferences),
        )

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class LoginMethod(StrEnum):
    PASSWORD = "password"
    OTP = "otp"


class VerificationPurpose(StrEnum):
    EMAIL_VERIFICATION = "email_verification"
    LOGIN_OTP = "login_otp"
    PASSWORD_RESET = "password_reset"


@dataclass(frozen=True, slots=True)
class AuthTokens:
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"


@dataclass(frozen=True, slots=True)
class AccessTokenIdentity:
    user_id: UUID
    session_id: UUID
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class RefreshTokenIdentity:
    user_id: UUID
    session_id: UUID
    expires_at: datetime


def normalize_email(value: str) -> str:
    return value.strip().lower()

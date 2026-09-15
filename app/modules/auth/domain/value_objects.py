from dataclasses import dataclass
from enum import StrEnum


class LoginMethod(StrEnum):
    PASSWORD = "password"
    OTP = "otp"


class VerificationPurpose(StrEnum):
    EMAIL_VERIFICATION = "email_verification"
    LOGIN_OTP = "login_otp"


@dataclass(frozen=True, slots=True)
class AuthTokens:
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"


def normalize_email(value: str) -> str:
    return value.strip().lower()

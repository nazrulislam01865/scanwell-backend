from dataclasses import dataclass
from uuid import UUID

from app.modules.auth.domain.value_objects import LoginMethod


@dataclass(frozen=True, slots=True)
class RegisterUserCommand:
    name: str
    email: str
    phone: str | None
    password: str
    preferred_login_method: LoginMethod


@dataclass(frozen=True, slots=True)
class VerifyEmailCommand:
    email: str
    code: str


@dataclass(frozen=True, slots=True)
class ResendVerificationCommand:
    email: str


@dataclass(frozen=True, slots=True)
class LoginUserCommand:
    email: str
    password: str


@dataclass(frozen=True, slots=True)
class RequestLoginOtpCommand:
    email: str


@dataclass(frozen=True, slots=True)
class VerifyLoginOtpCommand:
    email: str
    code: str


@dataclass(frozen=True, slots=True)
class RefreshTokenCommand:
    refresh_token: str


@dataclass(frozen=True, slots=True)
class ForgotPasswordCommand:
    email: str


@dataclass(frozen=True, slots=True)
class ResetPasswordCommand:
    email: str
    code: str
    new_password: str


@dataclass(frozen=True, slots=True)
class LogoutUserCommand:
    refresh_token: str


@dataclass(frozen=True, slots=True)
class LogoutAllCommand:
    user_id: UUID


from dataclasses import dataclass
from uuid import UUID

from app.modules.auth.domain.entities import AuthUser
from app.modules.auth.domain.value_objects import AuthTokens, LoginMethod


@dataclass(frozen=True, slots=True)
class AuthUserDTO:
    id: UUID
    name: str
    email: str
    phone: str | None
    preferred_login_method: LoginMethod
    email_verified: bool
    is_active: bool


@dataclass(frozen=True, slots=True)
class AuthResult:
    user: AuthUserDTO
    tokens: AuthTokens


@dataclass(frozen=True, slots=True)
class RegistrationResult:
    user: AuthUserDTO
    verification_required: bool
    development_verification_code: str | None = None


@dataclass(frozen=True, slots=True)
class CodeDispatchResult:
    accepted: bool = True
    message: str = "If the account is eligible, a verification code has been sent."
    development_verification_code: str | None = None


def to_user_dto(user: AuthUser) -> AuthUserDTO:
    return AuthUserDTO(
        id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        preferred_login_method=user.preferred_login_method,
        email_verified=user.email_verified,
        is_active=user.is_active,
    )

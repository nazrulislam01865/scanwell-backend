from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.modules.auth.application.dto import (
    AuthResult,
    AuthUserDTO,
    CodeDispatchResult,
    RegistrationResult,
)
from app.modules.auth.domain.value_objects import AuthTokens, LoginMethod


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=40)
    password: str = Field(min_length=6, max_length=128)
    preferred_login_method: LoginMethod = LoginMethod.PASSWORD


class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str = Field(pattern=r"^\d{6}$")


class EmailRequest(BaseModel):
    email: EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class UserResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    phone: str | None
    preferred_login_method: LoginMethod
    email_verified: bool
    is_active: bool

    @classmethod
    def from_dto(cls, user: AuthUserDTO) -> "UserResponse":
        return cls(
            id=user.id,
            name=user.name,
            email=user.email,
            phone=user.phone,
            preferred_login_method=user.preferred_login_method,
            email_verified=user.email_verified,
            is_active=user.is_active,
        )


class RegisterResponse(BaseModel):
    user: UserResponse
    verification_required: bool
    message: str = "Account created. Verify your email to continue."
    development_verification_code: str | None = None

    @classmethod
    def from_result(cls, result: RegistrationResult) -> "RegisterResponse":
        return cls(
            user=UserResponse.from_dto(result.user),
            verification_required=result.verification_required,
            development_verification_code=result.development_verification_code,
        )


class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

    @classmethod
    def from_result(cls, result: AuthResult) -> "AuthResponse":
        return cls(
            user=UserResponse.from_dto(result.user),
            access_token=result.tokens.access_token,
            refresh_token=result.tokens.refresh_token,
            token_type=result.tokens.token_type,
            expires_in=result.tokens.expires_in,
        )


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

    @classmethod
    def from_tokens(cls, tokens: AuthTokens) -> "TokenResponse":
        return cls(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            token_type=tokens.token_type,
            expires_in=tokens.expires_in,
        )


class CodeDispatchResponse(BaseModel):
    accepted: bool
    message: str
    development_verification_code: str | None = None

    @classmethod
    def from_result(cls, result: CodeDispatchResult) -> "CodeDispatchResponse":
        return cls(
            accepted=result.accepted,
            message=result.message,
            development_verification_code=result.development_verification_code,
        )

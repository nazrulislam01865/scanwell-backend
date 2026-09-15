from datetime import timedelta
from functools import lru_cache
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.core.config import settings
from app.core.database.transaction import SQLAlchemyTransaction
from app.core.security.jwt import JWTService

from app.modules.auth.application.code_service import VerificationCodeService
from app.modules.auth.application.use_cases.get_current_user import GetCurrentUser
from app.modules.auth.application.use_cases.login_user import LoginUser
from app.modules.auth.application.use_cases.refresh_token import RefreshToken
from app.modules.auth.application.use_cases.register_user import RegisterUser
from app.modules.auth.application.use_cases.request_login_otp import (
    RequestLoginOtp,
)
from app.modules.auth.application.use_cases.resend_verification import (
    ResendVerification,
)
from app.modules.auth.application.use_cases.verify_email import VerifyEmail
from app.modules.auth.application.use_cases.verify_login_otp import (
    VerifyLoginOtp,
)

from app.modules.auth.domain.exceptions import InvalidAuthTokenError
from app.modules.auth.domain.repositories import EmailService

from app.modules.auth.infrastructure.email_service import AuthEmailService
from app.modules.auth.infrastructure.repository import (
    SQLAlchemyUserRepository,
    SQLAlchemyVerificationCodeRepository,
)
from app.modules.auth.infrastructure.token_service import AuthTokenService

from app.shared.application.email import EmailSender
from app.shared.infrastructure.email.factory import build_email_sender


bearer_scheme = HTTPBearer(auto_error=False)


# ============================================================
# Shared / Cached Services
# ============================================================


@lru_cache
def get_verification_code_service() -> VerificationCodeService:
    """
    Provides the centralized verification-code service.

    Verification codes are secured using a dedicated secret derived
    from the main application secret.
    """

    return VerificationCodeService(
        f"{settings.secret_key}:verification-code"
    )


@lru_cache
def get_jwt_service() -> JWTService:
    """
    Provides the JWT service used for issuing and validating
    access and refresh tokens.
    """

    return JWTService(
        secret_key=settings.secret_key,
        algorithm=settings.jwt_algorithm,
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        access_token_ttl=timedelta(
            minutes=settings.access_token_minutes
        ),
        refresh_token_ttl=timedelta(
            days=settings.refresh_token_days
        ),
    )


@lru_cache
def get_auth_token_service() -> AuthTokenService:
    """
    Provides the auth token service.
    """

    return AuthTokenService(
        jwt_service=get_jwt_service(),
        access_expires_in=(
            settings.access_token_minutes * 60
        ),
    )


# ============================================================
# Centralized Email Services
# ============================================================


@lru_cache
def get_email_sender() -> EmailSender:
    """
    Creates the configured centralized email provider.

    Current supported providers:

    - log
    - smtp

    The provider itself is selected by EMAIL_DRIVER.

    Authentication/application code does not need to know which
    actual provider is being used.
    """

    return build_email_sender(settings)


@lru_cache
def get_email_service() -> EmailService:
    """
    Provides the authentication-specific email service.

    AuthEmailService handles authentication email content/templates.

    EmailSender handles the actual transport/provider.

    Flow:

        Auth use case
            -> AuthEmailService
            -> EmailSender
            -> SMTP / Log / future provider
    """

    return AuthEmailService(
        sender=get_email_sender(),
        code_ttl=timedelta(
            minutes=settings.verification_code_minutes
        ),
    )


# ============================================================
# Repository Factory
# ============================================================


def _repos(
    session: AsyncSession,
) -> tuple[
    SQLAlchemyUserRepository,
    SQLAlchemyVerificationCodeRepository,
]:
    """
    Creates repositories bound to the current request's
    database session.
    """

    users = SQLAlchemyUserRepository(session)

    codes = SQLAlchemyVerificationCodeRepository(
        session
    )

    return users, codes


# ============================================================
# Register User
# ============================================================


async def get_register_user_use_case(
    session: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
) -> RegisterUser:
    users, codes = _repos(session)

    return RegisterUser(
        users=users,
        codes=codes,
        transaction=SQLAlchemyTransaction(
            session
        ),
        email_service=get_email_service(),
        code_service=(
            get_verification_code_service()
        ),
        code_ttl=timedelta(
            minutes=(
                settings.verification_code_minutes
            )
        ),
        expose_development_code=(
            settings.expose_development_codes
        ),
    )


# ============================================================
# Verify Email
# ============================================================


async def get_verify_email_use_case(
    session: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
) -> VerifyEmail:
    users, codes = _repos(session)

    return VerifyEmail(
        users=users,
        codes=codes,
        transaction=SQLAlchemyTransaction(
            session
        ),
        code_service=(
            get_verification_code_service()
        ),
        token_service=(
            get_auth_token_service()
        ),
        max_attempts=(
            settings
            .verification_code_max_attempts
        ),
    )


# ============================================================
# Resend Email Verification
# ============================================================


async def get_resend_verification_use_case(
    session: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
) -> ResendVerification:
    users, codes = _repos(session)

    return ResendVerification(
        users=users,
        codes=codes,
        transaction=SQLAlchemyTransaction(
            session
        ),
        email_service=get_email_service(),
        code_service=(
            get_verification_code_service()
        ),
        code_ttl=timedelta(
            minutes=(
                settings.verification_code_minutes
            )
        ),
        expose_development_code=(
            settings.expose_development_codes
        ),
    )


# ============================================================
# Password Login
# ============================================================


async def get_login_user_use_case(
    session: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
) -> LoginUser:
    users, _codes = _repos(session)

    return LoginUser(
        users=users,
        token_service=(
            get_auth_token_service()
        ),
    )


# ============================================================
# Request Login OTP
# ============================================================


async def get_request_login_otp_use_case(
    session: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
) -> RequestLoginOtp:
    users, codes = _repos(session)

    return RequestLoginOtp(
        users=users,
        codes=codes,
        transaction=SQLAlchemyTransaction(
            session
        ),
        email_service=get_email_service(),
        code_service=(
            get_verification_code_service()
        ),
        code_ttl=timedelta(
            minutes=(
                settings.verification_code_minutes
            )
        ),
        expose_development_code=(
            settings.expose_development_codes
        ),
    )


# ============================================================
# Verify Login OTP
# ============================================================


async def get_verify_login_otp_use_case(
    session: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
) -> VerifyLoginOtp:
    users, codes = _repos(session)

    return VerifyLoginOtp(
        users=users,
        codes=codes,
        transaction=SQLAlchemyTransaction(
            session
        ),
        code_service=(
            get_verification_code_service()
        ),
        token_service=(
            get_auth_token_service()
        ),
        max_attempts=(
            settings
            .verification_code_max_attempts
        ),
    )


# ============================================================
# Refresh Token
# ============================================================


async def get_refresh_token_use_case(
    session: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
) -> RefreshToken:
    users, _codes = _repos(session)

    return RefreshToken(
        users=users,
        token_service=(
            get_auth_token_service()
        ),
    )


# ============================================================
# Current Authenticated User ID
# ============================================================


async def get_current_user_id(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> UUID:
    """
    Extracts the authenticated user's UUID from
    the Bearer access token.

    User identities remain UUID-based.
    """

    if (
        credentials is None
        or credentials.scheme.lower()
        != "bearer"
    ):
        raise InvalidAuthTokenError

    return (
        get_auth_token_service()
        .subject_from_access(
            credentials.credentials
        )
    )


# ============================================================
# Get Current User
# ============================================================


async def get_get_current_user_use_case(
    session: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
) -> GetCurrentUser:
    users, _codes = _repos(session)

    return GetCurrentUser(
        users=users
    )
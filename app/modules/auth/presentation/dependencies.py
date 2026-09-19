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
from app.modules.auth.application.session_service import AuthSessionService
from app.modules.auth.application.use_cases.forgot_password import ForgotPassword
from app.modules.auth.application.use_cases.get_current_user import GetCurrentUser
from app.modules.auth.application.use_cases.login_user import LoginUser
from app.modules.auth.application.use_cases.logout_all import LogoutAll
from app.modules.auth.application.use_cases.logout_user import LogoutUser
from app.modules.auth.application.use_cases.refresh_token import RefreshToken
from app.modules.auth.application.use_cases.register_user import RegisterUser
from app.modules.auth.application.use_cases.request_login_otp import RequestLoginOtp
from app.modules.auth.application.use_cases.resend_verification import ResendVerification
from app.modules.auth.application.use_cases.reset_password import ResetPassword
from app.modules.auth.application.use_cases.verify_email import VerifyEmail
from app.modules.auth.application.use_cases.verify_login_otp import VerifyLoginOtp
from app.modules.auth.domain.exceptions import InvalidAuthTokenError
from app.modules.auth.domain.repositories import EmailService
from app.modules.auth.infrastructure.email_service import AuthEmailService
from app.modules.auth.infrastructure.repository import (
    SQLAlchemyAuthSessionRepository,
    SQLAlchemyUserRepository,
    SQLAlchemyVerificationCodeRepository,
)
from app.modules.auth.infrastructure.token_service import AuthTokenService
from app.shared.application.email import EmailSender
from app.shared.infrastructure.email.factory import build_email_sender

bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache
def get_verification_code_service() -> VerificationCodeService:
    return VerificationCodeService(f"{settings.secret_key}:verification-code")


@lru_cache
def get_jwt_service() -> JWTService:
    return JWTService(
        secret_key=settings.secret_key,
        algorithm=settings.jwt_algorithm,
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        access_token_ttl=timedelta(minutes=settings.access_token_minutes),
        refresh_token_ttl=timedelta(days=settings.refresh_token_days),
    )


@lru_cache
def get_auth_token_service() -> AuthTokenService:
    return AuthTokenService(
        jwt_service=get_jwt_service(),
        access_expires_in=settings.access_token_minutes * 60,
    )


@lru_cache
def get_email_sender() -> EmailSender:
    return build_email_sender(settings)


@lru_cache
def get_email_service() -> EmailService:
    return AuthEmailService(
        sender=get_email_sender(),
        code_ttl=timedelta(minutes=settings.verification_code_minutes),
    )


def _repos(
    session: AsyncSession,
) -> tuple[SQLAlchemyUserRepository, SQLAlchemyVerificationCodeRepository]:
    return SQLAlchemyUserRepository(session), SQLAlchemyVerificationCodeRepository(session)


def _auth_session_repository(session: AsyncSession) -> SQLAlchemyAuthSessionRepository:
    return SQLAlchemyAuthSessionRepository(session)


def _auth_session_service(session: AsyncSession) -> AuthSessionService:
    return AuthSessionService(
        sessions=_auth_session_repository(session),
        token_service=get_auth_token_service(),
    )


async def get_register_user_use_case(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> RegisterUser:
    users, codes = _repos(session)
    return RegisterUser(
        users=users,
        codes=codes,
        transaction=SQLAlchemyTransaction(session),
        email_service=get_email_service(),
        code_service=get_verification_code_service(),
        code_ttl=timedelta(minutes=settings.verification_code_minutes),
        expose_development_code=settings.expose_development_codes,
    )


async def get_verify_email_use_case(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> VerifyEmail:
    users, codes = _repos(session)
    return VerifyEmail(
        users=users,
        codes=codes,
        transaction=SQLAlchemyTransaction(session),
        code_service=get_verification_code_service(),
        sessions=_auth_session_service(session),
        max_attempts=settings.verification_code_max_attempts,
    )


async def get_resend_verification_use_case(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ResendVerification:
    users, codes = _repos(session)
    return ResendVerification(
        users=users,
        codes=codes,
        transaction=SQLAlchemyTransaction(session),
        email_service=get_email_service(),
        code_service=get_verification_code_service(),
        code_ttl=timedelta(minutes=settings.verification_code_minutes),
        expose_development_code=settings.expose_development_codes,
    )


async def get_login_user_use_case(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> LoginUser:
    users, _codes = _repos(session)
    return LoginUser(
        users=users,
        sessions=_auth_session_service(session),
        transaction=SQLAlchemyTransaction(session),
    )


async def get_request_login_otp_use_case(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> RequestLoginOtp:
    users, codes = _repos(session)
    return RequestLoginOtp(
        users=users,
        codes=codes,
        transaction=SQLAlchemyTransaction(session),
        email_service=get_email_service(),
        code_service=get_verification_code_service(),
        code_ttl=timedelta(minutes=settings.verification_code_minutes),
        expose_development_code=settings.expose_development_codes,
    )


async def get_verify_login_otp_use_case(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> VerifyLoginOtp:
    users, codes = _repos(session)
    return VerifyLoginOtp(
        users=users,
        codes=codes,
        transaction=SQLAlchemyTransaction(session),
        code_service=get_verification_code_service(),
        sessions=_auth_session_service(session),
        max_attempts=settings.verification_code_max_attempts,
    )


async def get_refresh_token_use_case(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> RefreshToken:
    users, _codes = _repos(session)
    return RefreshToken(
        users=users,
        sessions=_auth_session_service(session),
        transaction=SQLAlchemyTransaction(session),
    )


async def get_logout_user_use_case(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> LogoutUser:
    return LogoutUser(
        sessions=_auth_session_service(session),
        transaction=SQLAlchemyTransaction(session),
    )


async def get_logout_all_use_case(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> LogoutAll:
    return LogoutAll(
        sessions=_auth_session_repository(session),
        transaction=SQLAlchemyTransaction(session),
    )


async def get_current_user_id(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> UUID:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise InvalidAuthTokenError
    return get_auth_token_service().subject_from_access(credentials.credentials)


async def get_get_current_user_use_case(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> GetCurrentUser:
    users, _codes = _repos(session)
    return GetCurrentUser(users=users)


async def get_forgot_password_use_case(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ForgotPassword:
    users, codes = _repos(session)
    return ForgotPassword(
        users=users,
        codes=codes,
        transaction=SQLAlchemyTransaction(session),
        email_service=get_email_service(),
        code_service=get_verification_code_service(),
        code_ttl=timedelta(minutes=settings.verification_code_minutes),
        expose_development_code=settings.expose_development_codes,
    )


async def get_reset_password_use_case(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ResetPassword:
    users, codes = _repos(session)
    return ResetPassword(
        users=users,
        codes=codes,
        sessions=_auth_session_repository(session),
        transaction=SQLAlchemyTransaction(session),
        code_service=get_verification_code_service(),
        max_attempts=settings.verification_code_max_attempts,
    )

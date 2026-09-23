from datetime import timedelta
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.core.config import settings
from app.core.database.transaction import SQLAlchemyTransaction
from app.core.security.jwt import JWTService
from app.modules.auth.application.admin_dto import AdminDTO
from app.modules.auth.application.session_service import AuthSessionService
from app.modules.auth.application.use_cases.get_current_admin import GetCurrentAdmin
from app.modules.auth.application.use_cases.login_admin import LoginAdmin
from app.modules.auth.application.use_cases.logout_user import LogoutUser
from app.modules.auth.application.use_cases.refresh_token import RefreshToken
from app.modules.auth.domain.exceptions import InvalidAuthTokenError
from app.modules.auth.infrastructure.admin_repository import (
    SQLAlchemyAdminAuthSessionRepository,
    SQLAlchemyAdminRepository,
)
from app.modules.auth.infrastructure.token_service import AuthTokenService

admin_bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache
def get_admin_jwt_service() -> JWTService:
    return JWTService(
        secret_key=settings.secret_key,
        algorithm=settings.jwt_algorithm,
        issuer=settings.jwt_issuer,
        audience=f"{settings.jwt_audience}:admin",
        access_token_ttl=timedelta(minutes=settings.access_token_minutes),
        refresh_token_ttl=timedelta(days=settings.refresh_token_days),
    )


@lru_cache
def get_admin_token_service() -> AuthTokenService:
    return AuthTokenService(
        jwt_service=get_admin_jwt_service(),
        access_expires_in=settings.access_token_minutes * 60,
    )


def _admin_repository(session: AsyncSession) -> SQLAlchemyAdminRepository:
    return SQLAlchemyAdminRepository(session)


def _admin_session_repository(
    session: AsyncSession,
) -> SQLAlchemyAdminAuthSessionRepository:
    return SQLAlchemyAdminAuthSessionRepository(session)


def _admin_session_service(session: AsyncSession) -> AuthSessionService:
    return AuthSessionService(
        sessions=_admin_session_repository(session),
        token_service=get_admin_token_service(),
    )


async def get_admin_login_use_case(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> LoginAdmin:
    return LoginAdmin(
        admins=_admin_repository(session),
        sessions=_admin_session_service(session),
        transaction=SQLAlchemyTransaction(session),
    )


async def get_admin_refresh_use_case(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> RefreshToken:
    return RefreshToken(
        users=_admin_repository(session),
        sessions=_admin_session_service(session),
        transaction=SQLAlchemyTransaction(session),
    )


async def get_admin_logout_use_case(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> LogoutUser:
    return LogoutUser(
        sessions=_admin_session_service(session),
        transaction=SQLAlchemyTransaction(session),
    )


async def get_current_admin_use_case(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> GetCurrentAdmin:
    return GetCurrentAdmin(
        admins=_admin_repository(session),
        sessions=_admin_session_repository(session),
        token_service=get_admin_token_service(),
    )


async def get_current_admin(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(admin_bearer_scheme),
    ],
    use_case: Annotated[GetCurrentAdmin, Depends(get_current_admin_use_case)],
) -> AdminDTO:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise InvalidAuthTokenError
    return await use_case.execute(credentials.credentials)

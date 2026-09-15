from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.domain.entities import AuthUser, VerificationCode
from app.modules.auth.domain.value_objects import LoginMethod, VerificationPurpose
from app.modules.auth.infrastructure.models import AuthUserModel, VerificationCodeModel


def user_model_to_entity(model: AuthUserModel) -> AuthUser:
    return AuthUser(
        id=model.id,
        name=model.name,
        email=model.email,
        phone=model.phone,
        password_hash=model.password_hash,
        preferred_login_method=LoginMethod(model.preferred_login_method),
        email_verified_at=model.email_verified_at,
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def verification_model_to_entity(model: VerificationCodeModel) -> VerificationCode:
    return VerificationCode(
        id=model.id,
        user_id=model.user_id,
        purpose=VerificationPurpose(model.purpose),
        code_hash=model.code_hash,
        expires_at=model.expires_at,
        consumed_at=model.consumed_at,
        failed_attempts=model.failed_attempts,
        created_at=model.created_at,
    )


class SQLAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> AuthUser | None:
        result = await self._session.execute(
            select(AuthUserModel).where(AuthUserModel.email == email)
        )
        model = result.scalar_one_or_none()
        return user_model_to_entity(model) if model is not None else None

    async def get_by_id(self, user_id: UUID) -> AuthUser | None:
        model = await self._session.get(AuthUserModel, user_id)
        return user_model_to_entity(model) if model is not None else None

    async def add(self, user: AuthUser) -> None:
        self._session.add(
            AuthUserModel(
                id=user.id,
                name=user.name,
                email=user.email,
                phone=user.phone,
                password_hash=user.password_hash,
                preferred_login_method=user.preferred_login_method.value,
                email_verified_at=user.email_verified_at,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
        )

    async def save(self, user: AuthUser) -> None:
        await self._session.execute(
            update(AuthUserModel)
            .where(AuthUserModel.id == user.id)
            .values(
                name=user.name,
                email=user.email,
                phone=user.phone,
                password_hash=user.password_hash,
                preferred_login_method=user.preferred_login_method.value,
                email_verified_at=user.email_verified_at,
                is_active=user.is_active,
                updated_at=user.updated_at,
            )
        )


class SQLAlchemyVerificationCodeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, code: VerificationCode) -> None:
        self._session.add(
            VerificationCodeModel(
                id=code.id,
                user_id=code.user_id,
                purpose=code.purpose.value,
                code_hash=code.code_hash,
                expires_at=code.expires_at,
                consumed_at=code.consumed_at,
                failed_attempts=code.failed_attempts,
                created_at=code.created_at,
            )
        )

    async def save(self, code: VerificationCode) -> None:
        await self._session.execute(
            update(VerificationCodeModel)
            .where(VerificationCodeModel.id == code.id)
            .values(
                consumed_at=code.consumed_at,
                failed_attempts=code.failed_attempts,
            )
        )

    async def get_latest_active(
        self,
        user_id: UUID,
        purpose: VerificationPurpose,
    ) -> VerificationCode | None:
        result = await self._session.execute(
            select(VerificationCodeModel)
            .where(
                VerificationCodeModel.user_id == user_id,
                VerificationCodeModel.purpose == purpose.value,
                VerificationCodeModel.consumed_at.is_(None),
            )
            .order_by(VerificationCodeModel.created_at.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return verification_model_to_entity(model) if model is not None else None

    async def invalidate_active(
        self,
        user_id: UUID,
        purpose: VerificationPurpose,
        consumed_at: datetime,
    ) -> None:
        await self._session.execute(
            update(VerificationCodeModel)
            .where(
                VerificationCodeModel.user_id == user_id,
                VerificationCodeModel.purpose == purpose.value,
                VerificationCodeModel.consumed_at.is_(None),
            )
            .values(consumed_at=consumed_at)
        )

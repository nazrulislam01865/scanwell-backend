from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.infrastructure.models import (
    AuthSessionModel,
    AuthUserModel,
    VerificationCodeModel,
)
from app.modules.users.domain.entities import UserAccount, UserPreferences
from app.modules.users.infrastructure.models import UserPreferenceModel


def user_model_to_account(model: AuthUserModel) -> UserAccount:
    return UserAccount(
        id=model.id,
        name=model.name,
        email=model.email,
        phone=model.phone,
        password_hash=model.password_hash,
        preferred_login_method=model.preferred_login_method,
        email_verified_at=model.email_verified_at,
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
        deleted_at=model.deleted_at,
    )


def preference_model_to_entity(model: UserPreferenceModel) -> UserPreferences:
    return UserPreferences(
        user_id=model.user_id,
        email_notifications=model.email_notifications,
        push_notifications=model.push_notifications,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SQLAlchemyUserAccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> UserAccount | None:
        model = await self._session.get(AuthUserModel, user_id)
        return user_model_to_account(model) if model is not None else None

    async def save(self, user: UserAccount) -> None:
        await self._session.execute(
            update(AuthUserModel)
            .where(AuthUserModel.id == user.id)
            .values(
                name=user.name,
                email=user.email,
                phone=user.phone,
                password_hash=user.password_hash,
                preferred_login_method=user.preferred_login_method,
                email_verified_at=user.email_verified_at,
                is_active=user.is_active,
                updated_at=user.updated_at,
                deleted_at=user.deleted_at,
            )
        )


class SQLAlchemyUserPreferencesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_id(self, user_id: UUID) -> UserPreferences | None:
        model = await self._session.get(UserPreferenceModel, user_id)
        return preference_model_to_entity(model) if model is not None else None

    async def add(self, preferences: UserPreferences) -> None:
        self._session.add(
            UserPreferenceModel(
                user_id=preferences.user_id,
                email_notifications=preferences.email_notifications,
                push_notifications=preferences.push_notifications,
                created_at=preferences.created_at,
                updated_at=preferences.updated_at,
            )
        )

    async def save(self, preferences: UserPreferences) -> None:
        await self._session.execute(
            update(UserPreferenceModel)
            .where(UserPreferenceModel.user_id == preferences.user_id)
            .values(
                email_notifications=preferences.email_notifications,
                push_notifications=preferences.push_notifications,
                updated_at=preferences.updated_at,
            )
        )

    async def delete_for_user(self, user_id: UUID) -> None:
        await self._session.execute(
            delete(UserPreferenceModel).where(UserPreferenceModel.user_id == user_id)
        )


class SQLAlchemyUserSecurityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def revoke_all_sessions(
        self,
        user_id: UUID,
        *,
        revoked_at: datetime,
        reason: str,
    ) -> None:
        await self._session.execute(
            update(AuthSessionModel)
            .where(
                AuthSessionModel.user_id == user_id,
                AuthSessionModel.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at, revoked_reason=reason)
        )

    async def invalidate_all_verification_codes(
        self,
        user_id: UUID,
        *,
        consumed_at: datetime,
    ) -> None:
        await self._session.execute(
            update(VerificationCodeModel)
            .where(
                VerificationCodeModel.user_id == user_id,
                VerificationCodeModel.consumed_at.is_(None),
            )
            .values(consumed_at=consumed_at)
        )

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.domain.admin_entities import Admin
from app.modules.auth.domain.entities import AuthSession
from app.modules.auth.infrastructure.models import AdminAuthSessionModel, AdminModel


def admin_model_to_entity(model: AdminModel) -> Admin:
    return Admin(
        id=model.id,
        name=model.name,
        email=model.email,
        password_hash=model.password_hash,
        role=model.role,
        status=model.status,
        last_login_at=model.last_login_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def admin_session_model_to_entity(model: AdminAuthSessionModel) -> AuthSession:
    return AuthSession(
        id=model.id,
        user_id=model.admin_id,
        refresh_token_hash=model.refresh_token_hash,
        expires_at=model.expires_at,
        created_at=model.created_at,
        last_used_at=model.last_used_at,
        revoked_at=model.revoked_at,
        revoked_reason=model.revoked_reason,
    )


class SQLAlchemyAdminRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, admin: Admin) -> None:
        self._session.add(
            AdminModel(
                id=admin.id,
                name=admin.name,
                email=admin.email,
                password_hash=admin.password_hash,
                role=admin.role,
                status=admin.status,
                last_login_at=admin.last_login_at,
                created_at=admin.created_at,
                updated_at=admin.updated_at,
            )
        )

    async def get_by_email(self, email: str) -> Admin | None:
        result = await self._session.execute(
            select(AdminModel).where(AdminModel.email == email).limit(1)
        )
        model = result.scalar_one_or_none()
        return admin_model_to_entity(model) if model is not None else None

    async def get_by_id(self, admin_id: UUID) -> Admin | None:
        model = await self._session.get(AdminModel, admin_id)
        return admin_model_to_entity(model) if model is not None else None

    async def save(self, admin: Admin) -> None:
        await self._session.execute(
            update(AdminModel)
            .where(AdminModel.id == admin.id)
            .values(
                name=admin.name,
                email=admin.email,
                password_hash=admin.password_hash,
                role=admin.role,
                status=admin.status,
                last_login_at=admin.last_login_at,
                updated_at=admin.updated_at,
            )
        )


class SQLAlchemyAdminAuthSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, auth_session: AuthSession) -> None:
        self._session.add(
            AdminAuthSessionModel(
                id=auth_session.id,
                admin_id=auth_session.user_id,
                refresh_token_hash=auth_session.refresh_token_hash,
                expires_at=auth_session.expires_at,
                created_at=auth_session.created_at,
                last_used_at=auth_session.last_used_at,
                revoked_at=auth_session.revoked_at,
                revoked_reason=auth_session.revoked_reason,
            )
        )

    async def save(self, auth_session: AuthSession) -> None:
        await self._session.execute(
            update(AdminAuthSessionModel)
            .where(AdminAuthSessionModel.id == auth_session.id)
            .values(
                refresh_token_hash=auth_session.refresh_token_hash,
                expires_at=auth_session.expires_at,
                last_used_at=auth_session.last_used_at,
                revoked_at=auth_session.revoked_at,
                revoked_reason=auth_session.revoked_reason,
            )
        )

    async def get_by_id(self, session_id: UUID) -> AuthSession | None:
        model = await self._session.get(AdminAuthSessionModel, session_id)
        return admin_session_model_to_entity(model) if model is not None else None

    async def revoke_all_for_user(
        self,
        user_id: UUID,
        *,
        revoked_at,
        reason: str,
    ) -> None:
        await self._session.execute(
            update(AdminAuthSessionModel)
            .where(
                AdminAuthSessionModel.admin_id == user_id,
                AdminAuthSessionModel.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at, revoked_reason=reason)
        )

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.auth.domain.admin_entities import Admin
from app.modules.auth.domain.value_objects import AuthTokens


@dataclass(frozen=True, slots=True)
class AdminDTO:
    id: UUID
    name: str
    email: str
    role: str
    status: str
    last_login_at: datetime | None


@dataclass(frozen=True, slots=True)
class AdminAuthResult:
    admin: AdminDTO
    tokens: AuthTokens


def to_admin_dto(admin: Admin) -> AdminDTO:
    return AdminDTO(
        id=admin.id,
        name=admin.name,
        email=admin.email,
        role=admin.role,
        status=admin.status,
        last_login_at=admin.last_login_at,
    )

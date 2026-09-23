from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.modules.auth.application.admin_dto import AdminAuthResult, AdminDTO


class AdminResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    role: str
    status: str
    last_login_at: datetime | None

    @classmethod
    def from_dto(cls, admin: AdminDTO) -> "AdminResponse":
        return cls(
            id=admin.id,
            name=admin.name,
            email=admin.email,
            role=admin.role,
            status=admin.status,
            last_login_at=admin.last_login_at,
        )


class AdminAuthResponse(BaseModel):
    admin: AdminResponse
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

    @classmethod
    def from_result(cls, result: AdminAuthResult) -> "AdminAuthResponse":
        return cls(
            admin=AdminResponse.from_dto(result.admin),
            access_token=result.tokens.access_token,
            refresh_token=result.tokens.refresh_token,
            token_type=result.tokens.token_type,
            expires_in=result.tokens.expires_in,
        )

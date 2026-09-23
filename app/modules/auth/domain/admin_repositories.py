from typing import Protocol
from uuid import UUID

from app.modules.auth.domain.admin_entities import Admin


class AdminRepository(Protocol):
    async def get_by_email(self, email: str) -> Admin | None: ...

    async def get_by_id(self, admin_id: UUID) -> Admin | None: ...

    async def save(self, admin: Admin) -> None: ...

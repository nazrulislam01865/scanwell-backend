from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.modules.users.domain.entities import UserAccount, UserPreferences


class UserAccountRepository(Protocol):
    async def get_by_id(self, user_id: UUID) -> UserAccount | None: ...

    async def save(self, user: UserAccount) -> None: ...


class UserPreferencesRepository(Protocol):
    async def get_by_user_id(self, user_id: UUID) -> UserPreferences | None: ...

    async def add(self, preferences: UserPreferences) -> None: ...

    async def save(self, preferences: UserPreferences) -> None: ...

    async def delete_for_user(self, user_id: UUID) -> None: ...


class UserSecurityRepository(Protocol):
    async def revoke_all_sessions(
        self,
        user_id: UUID,
        *,
        revoked_at: datetime,
        reason: str,
    ) -> None: ...

    async def invalidate_all_verification_codes(
        self,
        user_id: UUID,
        *,
        consumed_at: datetime,
    ) -> None: ...

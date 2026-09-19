from datetime import datetime
from uuid import UUID

from app.modules.users.domain.entities import UserAccount, UserPreferences


class InMemoryUserAccountRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, UserAccount] = {}
        self.saved_ids: list[UUID] = []

    async def get_by_id(self, user_id: UUID) -> UserAccount | None:
        return self.items.get(user_id)

    async def save(self, user: UserAccount) -> None:
        self.items[user.id] = user
        self.saved_ids.append(user.id)


class InMemoryUserPreferencesRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, UserPreferences] = {}
        self.deleted_ids: list[UUID] = []

    async def get_by_user_id(self, user_id: UUID) -> UserPreferences | None:
        return self.items.get(user_id)

    async def add(self, preferences: UserPreferences) -> None:
        self.items[preferences.user_id] = preferences

    async def save(self, preferences: UserPreferences) -> None:
        self.items[preferences.user_id] = preferences

    async def delete_for_user(self, user_id: UUID) -> None:
        self.items.pop(user_id, None)
        self.deleted_ids.append(user_id)


class InMemoryUserSecurityRepository:
    def __init__(self) -> None:
        self.revocations: list[tuple[UUID, datetime, str]] = []
        self.invalidations: list[tuple[UUID, datetime]] = []

    async def revoke_all_sessions(
        self,
        user_id: UUID,
        *,
        revoked_at: datetime,
        reason: str,
    ) -> None:
        self.revocations.append((user_id, revoked_at, reason))

    async def invalidate_all_verification_codes(
        self,
        user_id: UUID,
        *,
        consumed_at: datetime,
    ) -> None:
        self.invalidations.append((user_id, consumed_at))


class FakeTransaction:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.core.security.passwords import hash_password
from app.modules.auth.application.queries import CurrentUserQuery
from app.modules.auth.application.use_cases.get_current_user import GetCurrentUser
from app.modules.auth.domain.entities import AuthUser
from app.modules.auth.domain.value_objects import LoginMethod
from tests.unit.auth.fakes import InMemoryUserRepository


@pytest.mark.asyncio
async def test_get_current_user_returns_public_user_dto() -> None:
    now = datetime.now(UTC)
    users = InMemoryUserRepository()
    user = AuthUser(
        id=uuid4(),
        name="Nazrul",
        email="nazrul@example.com",
        phone=None,
        password_hash=hash_password("secret123"),
        preferred_login_method=LoginMethod.PASSWORD,
        email_verified_at=now,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    await users.add(user)

    result = await GetCurrentUser(users=users).execute(CurrentUserQuery(user_id=user.id))

    assert result.id == user.id
    assert result.email == user.email
    assert result.email_verified is True

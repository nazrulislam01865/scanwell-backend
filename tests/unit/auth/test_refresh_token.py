from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.core.security.passwords import hash_password
from app.modules.auth.application.commands import RefreshTokenCommand
from app.modules.auth.application.use_cases.refresh_token import RefreshToken
from app.modules.auth.domain.entities import AuthUser
from app.modules.auth.domain.value_objects import LoginMethod
from tests.unit.auth.fakes import FakeTokenService, InMemoryUserRepository


@pytest.mark.asyncio
async def test_refresh_token_rotates_pair_for_active_user() -> None:
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
    tokens = FakeTokenService()
    use_case = RefreshToken(users=users, token_service=tokens)

    result = await use_case.execute(
        RefreshTokenCommand(refresh_token=f"refresh:{user.id}")
    )

    assert result.access_token == f"access:{user.id}"
    assert result.refresh_token == f"refresh:{user.id}"

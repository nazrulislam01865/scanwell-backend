from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.core.security.passwords import hash_password
from app.modules.auth.application.commands import LoginUserCommand
from app.modules.auth.application.use_cases.login_user import LoginUser
from app.modules.auth.domain.entities import AuthUser
from app.modules.auth.domain.exceptions import EmailNotVerifiedError, InvalidCredentialsError
from app.modules.auth.domain.value_objects import LoginMethod
from tests.unit.auth.fakes import FakeTokenService, InMemoryUserRepository


@pytest.mark.asyncio
async def test_password_login_returns_tokens_for_verified_user() -> None:
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
    use_case = LoginUser(users=users, token_service=FakeTokenService())

    result = await use_case.execute(
        LoginUserCommand(email="NAZRUL@example.com", password="secret123")
    )

    assert result.user.id == user.id
    assert result.tokens.access_token == f"access:{user.id}"


@pytest.mark.asyncio
async def test_password_login_rejects_bad_password() -> None:
    now = datetime.now(UTC)
    users = InMemoryUserRepository()
    await users.add(
        AuthUser(
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
    )
    use_case = LoginUser(users=users, token_service=FakeTokenService())

    with pytest.raises(InvalidCredentialsError):
        await use_case.execute(
            LoginUserCommand(email="nazrul@example.com", password="wrong-password")
        )


@pytest.mark.asyncio
async def test_password_login_requires_verified_email() -> None:
    now = datetime.now(UTC)
    users = InMemoryUserRepository()
    await users.add(
        AuthUser(
            id=uuid4(),
            name="Nazrul",
            email="nazrul@example.com",
            phone=None,
            password_hash=hash_password("secret123"),
            preferred_login_method=LoginMethod.PASSWORD,
            email_verified_at=None,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
    )
    use_case = LoginUser(users=users, token_service=FakeTokenService())

    with pytest.raises(EmailNotVerifiedError):
        await use_case.execute(
            LoginUserCommand(email="nazrul@example.com", password="secret123")
        )

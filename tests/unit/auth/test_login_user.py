from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.core.security.passwords import hash_password
from app.modules.auth.application.commands import LoginUserCommand
from app.modules.auth.application.session_service import AuthSessionService
from app.modules.auth.application.use_cases.login_user import LoginUser
from app.modules.auth.domain.entities import AuthUser
from app.modules.auth.domain.exceptions import EmailNotVerifiedError, InvalidCredentialsError
from app.modules.auth.domain.value_objects import LoginMethod
from tests.unit.auth.fakes import (
    FakeTokenService,
    FakeTransaction,
    InMemoryAuthSessionRepository,
    InMemoryUserRepository,
)


def build_login(users: InMemoryUserRepository):
    session_repo = InMemoryAuthSessionRepository()
    tx = FakeTransaction()
    use_case = LoginUser(
        users=users,
        sessions=AuthSessionService(
            sessions=session_repo,
            token_service=FakeTokenService(),
        ),
        transaction=tx,
    )
    return use_case, session_repo, tx


@pytest.mark.asyncio
async def test_password_login_returns_tokens_and_persists_session() -> None:
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
    use_case, sessions, tx = build_login(users)

    result = await use_case.execute(
        LoginUserCommand(email="NAZRUL@example.com", password="secret123")
    )

    assert result.user.id == user.id
    assert result.tokens.access_token.startswith(f"access:{user.id}:")
    assert len(sessions.items) == 1
    session = next(iter(sessions.items.values()))
    assert session.user_id == user.id
    assert session.refresh_token_hash != result.tokens.refresh_token
    assert tx.commits == 1


@pytest.mark.asyncio
async def test_password_login_rejects_bad_password_without_session() -> None:
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
    use_case, sessions, tx = build_login(users)

    with pytest.raises(InvalidCredentialsError):
        await use_case.execute(
            LoginUserCommand(email="nazrul@example.com", password="wrong-password")
        )

    assert sessions.items == {}
    assert tx.commits == 0


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
    use_case, sessions, _tx = build_login(users)

    with pytest.raises(EmailNotVerifiedError):
        await use_case.execute(
            LoginUserCommand(email="nazrul@example.com", password="secret123")
        )

    assert sessions.items == {}

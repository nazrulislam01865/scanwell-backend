from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.core.security.passwords import hash_password
from app.modules.auth.application.commands import RefreshTokenCommand
from app.modules.auth.application.session_service import AuthSessionService
from app.modules.auth.application.use_cases.refresh_token import RefreshToken
from app.modules.auth.domain.entities import AuthUser
from app.modules.auth.domain.exceptions import InvalidAuthTokenError
from app.modules.auth.domain.value_objects import LoginMethod
from tests.unit.auth.fakes import (
    FakeTokenService,
    FakeTransaction,
    InMemoryAuthSessionRepository,
    InMemoryUserRepository,
)


@pytest.mark.asyncio
async def test_refresh_token_rotates_stored_token_for_active_session() -> None:
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

    session_repo = InMemoryAuthSessionRepository()
    token_service = FakeTokenService()
    sessions = AuthSessionService(sessions=session_repo, token_service=token_service)
    initial = await sessions.issue(user_id=user.id)
    old_refresh = initial.refresh_token
    session = next(iter(session_repo.items.values()))
    old_hash = session.refresh_token_hash

    tx = FakeTransaction()
    use_case = RefreshToken(users=users, sessions=sessions, transaction=tx)
    result = await use_case.execute(RefreshTokenCommand(refresh_token=old_refresh))

    assert result.refresh_token != old_refresh
    assert session.refresh_token_hash != old_hash
    assert token_service.refresh_token_matches(result.refresh_token, session.refresh_token_hash)
    assert tx.commits == 1

    with pytest.raises(InvalidAuthTokenError):
        await use_case.execute(RefreshTokenCommand(refresh_token=old_refresh))

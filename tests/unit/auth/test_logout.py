from uuid import uuid4

import pytest

from app.modules.auth.application.commands import LogoutAllCommand, LogoutUserCommand
from app.modules.auth.application.session_service import AuthSessionService
from app.modules.auth.application.use_cases.logout_all import LogoutAll
from app.modules.auth.application.use_cases.logout_user import LogoutUser
from app.modules.auth.domain.exceptions import AuthSessionRevokedError
from tests.unit.auth.fakes import (
    FakeTokenService,
    FakeTransaction,
    InMemoryAuthSessionRepository,
)


@pytest.mark.asyncio
async def test_logout_revokes_current_refresh_session() -> None:
    repo = InMemoryAuthSessionRepository()
    service = AuthSessionService(sessions=repo, token_service=FakeTokenService())
    tokens = await service.issue(user_id=uuid4())
    session = next(iter(repo.items.values()))
    tx = FakeTransaction()

    use_case = LogoutUser(sessions=service, transaction=tx)
    await use_case.execute(LogoutUserCommand(refresh_token=tokens.refresh_token))

    assert session.revoked is True
    assert session.revoked_reason == "logout"
    assert tx.commits == 1

    with pytest.raises(AuthSessionRevokedError):
        await service.rotate(refresh_token=tokens.refresh_token)


@pytest.mark.asyncio
async def test_logout_all_revokes_every_user_session_only() -> None:
    repo = InMemoryAuthSessionRepository()
    service = AuthSessionService(sessions=repo, token_service=FakeTokenService())
    user_id = uuid4()
    other_user_id = uuid4()
    await service.issue(user_id=user_id)
    await service.issue(user_id=user_id)
    await service.issue(user_id=other_user_id)
    tx = FakeTransaction()

    use_case = LogoutAll(sessions=repo, transaction=tx)
    await use_case.execute(LogoutAllCommand(user_id=user_id))

    own_sessions = [s for s in repo.items.values() if s.user_id == user_id]
    other_sessions = [s for s in repo.items.values() if s.user_id == other_user_id]
    assert all(s.revoked for s in own_sessions)
    assert all(s.revoked_reason == "logout_all" for s in own_sessions)
    assert all(not s.revoked for s in other_sessions)
    assert tx.commits == 1

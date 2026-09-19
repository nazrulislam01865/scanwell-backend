from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.core.security.passwords import hash_password, verify_password
from app.modules.auth.application.code_service import VerificationCodeService
from app.modules.auth.application.commands import ResetPasswordCommand
from app.modules.auth.application.session_service import AuthSessionService
from app.modules.auth.application.use_cases.reset_password import ResetPassword
from app.modules.auth.domain.entities import AuthUser, VerificationCode
from app.modules.auth.domain.value_objects import LoginMethod, VerificationPurpose
from tests.unit.auth.fakes import (
    FakeTokenService,
    FakeTransaction,
    InMemoryAuthSessionRepository,
    InMemoryUserRepository,
    InMemoryVerificationCodeRepository,
)


@pytest.mark.asyncio
async def test_password_reset_revokes_all_existing_sessions() -> None:
    now = datetime.now(UTC)
    users = InMemoryUserRepository()
    user = AuthUser(
        id=uuid4(),
        name="Nazrul",
        email="nazrul@example.com",
        phone=None,
        password_hash=hash_password("old-password"),
        preferred_login_method=LoginMethod.PASSWORD,
        email_verified_at=now,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    await users.add(user)

    session_repo = InMemoryAuthSessionRepository()
    session_service = AuthSessionService(
        sessions=session_repo,
        token_service=FakeTokenService(),
    )
    await session_service.issue(user_id=user.id)
    await session_service.issue(user_id=user.id)

    code_service = VerificationCodeService("test-code-secret")
    codes = InMemoryVerificationCodeRepository()
    raw_code = "123456"
    challenge_id = uuid4()
    challenge = VerificationCode(
        id=challenge_id,
        user_id=user.id,
        purpose=VerificationPurpose.PASSWORD_RESET,
        code_hash=code_service.digest(
            raw_code,
            challenge_id=challenge_id,
            user_id=user.id,
            purpose=VerificationPurpose.PASSWORD_RESET,
            created_at=now,
        ),
        expires_at=now + timedelta(minutes=10),
        consumed_at=None,
        failed_attempts=0,
        created_at=now,
    )
    await codes.add(challenge)

    use_case = ResetPassword(
        users=users,
        codes=codes,
        sessions=session_repo,
        transaction=FakeTransaction(),
        code_service=code_service,
        max_attempts=5,
    )
    await use_case.execute(
        ResetPasswordCommand(
            email=user.email,
            code=raw_code,
            new_password="new-password",
        )
    )

    assert verify_password("new-password", user.password_hash)
    assert challenge.consumed_at is not None
    assert all(session.revoked for session in session_repo.items.values())
    assert all(
        session.revoked_reason == "password_reset"
        for session in session_repo.items.values()
    )

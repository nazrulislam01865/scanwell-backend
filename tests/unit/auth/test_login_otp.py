from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.core.security.passwords import hash_password
from app.modules.auth.application.code_service import VerificationCodeService
from app.modules.auth.application.commands import RequestLoginOtpCommand, VerifyLoginOtpCommand
from app.modules.auth.application.session_service import AuthSessionService
from app.modules.auth.application.use_cases.request_login_otp import RequestLoginOtp
from app.modules.auth.application.use_cases.verify_login_otp import VerifyLoginOtp
from app.modules.auth.domain.entities import AuthUser
from app.modules.auth.domain.value_objects import LoginMethod, VerificationPurpose
from tests.unit.auth.fakes import (
    FakeEmailService,
    FakeTokenService,
    FakeTransaction,
    InMemoryAuthSessionRepository,
    InMemoryUserRepository,
    InMemoryVerificationCodeRepository,
)


@pytest.mark.asyncio
async def test_request_and_verify_login_otp_returns_tokens_and_creates_session() -> None:
    now = datetime.now(UTC)
    users = InMemoryUserRepository()
    codes = InMemoryVerificationCodeRepository()
    email = FakeEmailService()
    tx = FakeTransaction()
    user = AuthUser(
        id=uuid4(),
        name="Nazrul",
        email="nazrul@example.com",
        phone=None,
        password_hash=hash_password("secret123"),
        preferred_login_method=LoginMethod.OTP,
        email_verified_at=now,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    await users.add(user)
    code_service = VerificationCodeService("test-code-secret")
    request = RequestLoginOtp(
        users=users,
        codes=codes,
        transaction=tx,
        email_service=email,
        code_service=code_service,
        code_ttl=timedelta(minutes=10),
        expose_development_code=True,
    )

    dispatched = await request.execute(RequestLoginOtpCommand(email=user.email))

    assert dispatched.development_verification_code is not None
    assert email.sent[0][2] == VerificationPurpose.LOGIN_OTP

    session_repo = InMemoryAuthSessionRepository()
    verify = VerifyLoginOtp(
        users=users,
        codes=codes,
        transaction=tx,
        code_service=code_service,
        sessions=AuthSessionService(
            sessions=session_repo,
            token_service=FakeTokenService(),
        ),
        max_attempts=5,
    )
    result = await verify.execute(
        VerifyLoginOtpCommand(
            email=user.email,
            code=dispatched.development_verification_code,
        )
    )

    assert result.user.id == user.id
    assert result.tokens.access_token.startswith(f"access:{user.id}:")
    assert len(session_repo.items) == 1


@pytest.mark.asyncio
async def test_request_login_otp_is_generic_for_unknown_email() -> None:
    request = RequestLoginOtp(
        users=InMemoryUserRepository(),
        codes=InMemoryVerificationCodeRepository(),
        transaction=FakeTransaction(),
        email_service=FakeEmailService(),
        code_service=VerificationCodeService("test-code-secret"),
        code_ttl=timedelta(minutes=10),
        expose_development_code=True,
    )

    result = await request.execute(RequestLoginOtpCommand(email="missing@example.com"))

    assert result.accepted is True
    assert result.development_verification_code is None

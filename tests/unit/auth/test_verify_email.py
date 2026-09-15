from datetime import timedelta

import pytest

from app.modules.auth.application.code_service import VerificationCodeService
from app.modules.auth.application.commands import RegisterUserCommand, VerifyEmailCommand
from app.modules.auth.application.use_cases.register_user import RegisterUser
from app.modules.auth.application.use_cases.verify_email import VerifyEmail
from app.modules.auth.domain.exceptions import InvalidVerificationCodeError
from app.modules.auth.domain.value_objects import LoginMethod
from tests.unit.auth.fakes import (
    FakeEmailService,
    FakeTokenService,
    FakeTransaction,
    InMemoryUserRepository,
    InMemoryVerificationCodeRepository,
)


@pytest.mark.asyncio
async def test_verify_email_marks_user_verified_and_returns_tokens() -> None:
    users = InMemoryUserRepository()
    codes = InMemoryVerificationCodeRepository()
    email = FakeEmailService()
    tx = FakeTransaction()
    code_service = VerificationCodeService("test-code-secret")
    register = RegisterUser(
        users=users,
        codes=codes,
        transaction=tx,
        email_service=email,
        code_service=code_service,
        code_ttl=timedelta(minutes=10),
        expose_development_code=True,
    )
    registration = await register.execute(
        RegisterUserCommand(
            name="Nazrul",
            email="nazrul@example.com",
            phone=None,
            password="secret123",
            preferred_login_method=LoginMethod.PASSWORD,
        )
    )
    assert registration.development_verification_code is not None

    verify = VerifyEmail(
        users=users,
        codes=codes,
        transaction=tx,
        code_service=code_service,
        token_service=FakeTokenService(),
        max_attempts=5,
    )
    result = await verify.execute(
        VerifyEmailCommand(
            email="NAZRUL@example.com",
            code=registration.development_verification_code,
        )
    )

    assert result.user.email_verified is True
    assert result.tokens.access_token.startswith("access:")
    assert result.tokens.refresh_token.startswith("refresh:")
    assert result.user.id in users.saved_ids
    assert codes.items[-1].id in codes.saved_ids


@pytest.mark.asyncio
async def test_verify_email_rejects_wrong_code() -> None:
    users = InMemoryUserRepository()
    codes = InMemoryVerificationCodeRepository()
    email = FakeEmailService()
    tx = FakeTransaction()
    code_service = VerificationCodeService("test-code-secret")
    register = RegisterUser(
        users=users,
        codes=codes,
        transaction=tx,
        email_service=email,
        code_service=code_service,
        code_ttl=timedelta(minutes=10),
        expose_development_code=False,
    )
    await register.execute(
        RegisterUserCommand(
            name="Nazrul",
            email="nazrul@example.com",
            phone=None,
            password="secret123",
            preferred_login_method=LoginMethod.PASSWORD,
        )
    )
    verify = VerifyEmail(
        users=users,
        codes=codes,
        transaction=tx,
        code_service=code_service,
        token_service=FakeTokenService(),
        max_attempts=5,
    )

    with pytest.raises(InvalidVerificationCodeError):
        await verify.execute(
            VerifyEmailCommand(email="nazrul@example.com", code="000000")
        )

@pytest.mark.asyncio
async def test_verify_email_rejects_expired_code() -> None:
    from datetime import UTC, datetime, timedelta

    from app.modules.auth.domain.exceptions import VerificationCodeExpiredError

    users = InMemoryUserRepository()
    codes = InMemoryVerificationCodeRepository()
    email = FakeEmailService()
    tx = FakeTransaction()
    code_service = VerificationCodeService("test-code-secret")
    register = RegisterUser(
        users=users,
        codes=codes,
        transaction=tx,
        email_service=email,
        code_service=code_service,
        code_ttl=timedelta(minutes=10),
        expose_development_code=True,
    )
    registration = await register.execute(
        RegisterUserCommand(
            name="Nazrul",
            email="nazrul@example.com",
            phone=None,
            password="secret123",
            preferred_login_method=LoginMethod.PASSWORD,
        )
    )
    assert registration.development_verification_code is not None
    challenge = codes.items[-1]
    challenge.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    verify = VerifyEmail(
        users=users,
        codes=codes,
        transaction=tx,
        code_service=code_service,
        token_service=FakeTokenService(),
        max_attempts=5,
    )

    with pytest.raises(VerificationCodeExpiredError):
        await verify.execute(
            VerifyEmailCommand(
                email="nazrul@example.com",
                code=registration.development_verification_code,
            )
        )

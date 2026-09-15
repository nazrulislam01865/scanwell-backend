from datetime import timedelta

import pytest

from app.modules.auth.application.code_service import VerificationCodeService
from app.modules.auth.application.commands import RegisterUserCommand, ResendVerificationCommand
from app.modules.auth.application.use_cases.register_user import RegisterUser
from app.modules.auth.application.use_cases.resend_verification import ResendVerification
from app.modules.auth.domain.value_objects import LoginMethod
from tests.unit.auth.fakes import (
    FakeEmailService,
    FakeTransaction,
    InMemoryUserRepository,
    InMemoryVerificationCodeRepository,
)


@pytest.mark.asyncio
async def test_resend_verification_invalidates_previous_code() -> None:
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
    first = await register.execute(
        RegisterUserCommand(
            name="Nazrul",
            email="nazrul@example.com",
            phone=None,
            password="secret123",
            preferred_login_method=LoginMethod.PASSWORD,
        )
    )
    first_challenge = codes.items[-1]

    resend = ResendVerification(
        users=users,
        codes=codes,
        transaction=tx,
        email_service=email,
        code_service=code_service,
        code_ttl=timedelta(minutes=10),
        expose_development_code=True,
    )
    second = await resend.execute(
        ResendVerificationCommand(email="nazrul@example.com")
    )

    assert first.development_verification_code is not None
    assert second.development_verification_code is not None
    assert first_challenge.consumed_at is not None
    assert len(codes.items) == 2

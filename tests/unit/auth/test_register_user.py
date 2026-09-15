from datetime import timedelta

import pytest

from app.core.security.passwords import verify_password
from app.modules.auth.application.code_service import VerificationCodeService
from app.modules.auth.application.commands import RegisterUserCommand
from app.modules.auth.application.use_cases.register_user import RegisterUser
from app.modules.auth.domain.exceptions import EmailAlreadyRegisteredError
from app.modules.auth.domain.value_objects import LoginMethod, VerificationPurpose
from tests.unit.auth.fakes import (
    FakeEmailService,
    FakeTransaction,
    InMemoryUserRepository,
    InMemoryVerificationCodeRepository,
)


@pytest.mark.asyncio
async def test_register_user_creates_unverified_account_and_sends_code() -> None:
    users = InMemoryUserRepository()
    codes = InMemoryVerificationCodeRepository()
    email = FakeEmailService()
    tx = FakeTransaction()
    use_case = RegisterUser(
        users=users,
        codes=codes,
        transaction=tx,
        email_service=email,
        code_service=VerificationCodeService("test-code-secret"),
        code_ttl=timedelta(minutes=10),
        expose_development_code=True,
    )

    result = await use_case.execute(
        RegisterUserCommand(
            name=" Nazrul Islam ",
            email="NAZRUL@example.com ",
            phone=" +8801712345678 ",
            password="secret123",
            preferred_login_method=LoginMethod.OTP,
        )
    )

    stored = await users.get_by_email("nazrul@example.com")
    assert stored is not None
    assert stored.name == "Nazrul Islam"
    assert stored.phone == "+8801712345678"
    assert stored.email_verified_at is None
    assert stored.preferred_login_method == LoginMethod.OTP
    assert verify_password("secret123", stored.password_hash)
    assert email.sent[0][0] == "nazrul@example.com"
    assert email.sent[0][2] == VerificationPurpose.EMAIL_VERIFICATION
    assert result.development_verification_code == email.sent[0][1]
    assert tx.commits == 1


@pytest.mark.asyncio
async def test_register_user_rejects_duplicate_email() -> None:
    users = InMemoryUserRepository()
    codes = InMemoryVerificationCodeRepository()
    email = FakeEmailService()
    tx = FakeTransaction()
    use_case = RegisterUser(
        users=users,
        codes=codes,
        transaction=tx,
        email_service=email,
        code_service=VerificationCodeService("test-code-secret"),
        code_ttl=timedelta(minutes=10),
        expose_development_code=False,
    )
    command = RegisterUserCommand(
        name="Nazrul",
        email="nazrul@example.com",
        phone=None,
        password="secret123",
        preferred_login_method=LoginMethod.PASSWORD,
    )
    await use_case.execute(command)

    with pytest.raises(EmailAlreadyRegisteredError):
        await use_case.execute(command)

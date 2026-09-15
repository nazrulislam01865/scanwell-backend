from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.core.database.transaction import (
    TransactionManager,
)
from app.core.security.passwords import (
    hash_password,
)
from app.modules.auth.application.code_service import (
    VerificationCodeService,
)
from app.modules.auth.application.commands import (
    RegisterUserCommand,
)
from app.modules.auth.application.dto import (
    RegistrationResult,
    to_user_dto,
)
from app.modules.auth.domain.entities import (
    AuthUser,
    VerificationCode,
)
from app.modules.auth.domain.exceptions import (
    EmailAlreadyRegisteredError,
)
from app.modules.auth.domain.repositories import (
    EmailService,
    UserRepository,
    VerificationCodeRepository,
)
from app.modules.auth.domain.value_objects import (
    VerificationPurpose,
    normalize_email,
)


class RegisterUser:
    def __init__(
        self,
        *,
        users: UserRepository,
        codes: VerificationCodeRepository,
        transaction: TransactionManager,
        email_service: EmailService,
        code_service: VerificationCodeService,
        code_ttl: timedelta,
        expose_development_code: bool,
    ) -> None:

        self._users = users
        self._codes = codes

        self._transaction = transaction

        self._email_service = email_service

        self._code_service = code_service

        self._code_ttl = code_ttl

        self._expose_development_code = (
            expose_development_code
        )

    async def execute(
        self,
        command: RegisterUserCommand,
    ) -> RegistrationResult:

        email = normalize_email(
            command.email
        )

        if (
            await self._users.get_by_email(
                email
            )
            is not None
        ):
            raise EmailAlreadyRegisteredError

        now = datetime.now(UTC)

        user = AuthUser(
            id=uuid4(),
            name=command.name.strip(),
            email=email,
            phone=(
                (command.phone or "").strip()
                or None
            ),
            password_hash=hash_password(
                command.password
            ),
            preferred_login_method=(
                command.preferred_login_method
            ),
            email_verified_at=None,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        code = self._code_service.generate()

        # UUID verification challenge
        challenge_id = uuid4()

        purpose = (
            VerificationPurpose
            .EMAIL_VERIFICATION
        )

        challenge = VerificationCode(
            id=challenge_id,
            user_id=user.id,
            purpose=purpose,
            code_hash=(
                self._code_service.digest(
                    code,
                    challenge_id=challenge_id,
                    user_id=user.id,
                    purpose=purpose,
                    created_at=now,
                )
            ),
            expires_at=(
                now + self._code_ttl
            ),
            consumed_at=None,
            failed_attempts=0,
            created_at=now,
        )

        await self._users.add(user)

        await self._codes.add(
            challenge
        )

        await self._transaction.commit()

        await (
            self._email_service
            .send_verification_code(
                email=user.email,
                code=code,
                purpose=purpose,
            )
        )

        return RegistrationResult(
            user=to_user_dto(user),
            verification_required=True,
            development_verification_code=(
                code
                if self._expose_development_code
                else None
            ),
        )
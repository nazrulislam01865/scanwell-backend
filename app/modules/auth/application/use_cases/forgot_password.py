from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.core.database.transaction import TransactionManager
from app.modules.auth.application.code_service import VerificationCodeService
from app.modules.auth.application.commands import ForgotPasswordCommand
from app.modules.auth.application.dto import CodeDispatchResult
from app.modules.auth.domain.entities import VerificationCode
from app.modules.auth.domain.repositories import (
    EmailService,
    UserRepository,
    VerificationCodeRepository,
)
from app.modules.auth.domain.value_objects import VerificationPurpose, normalize_email


_PASSWORD_RESET_MESSAGE = (
    "If an eligible account exists for this email, a password reset code has been sent."
)


class ForgotPassword:
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
        self._expose_development_code = expose_development_code

    async def execute(
        self,
        command: ForgotPasswordCommand,
    ) -> CodeDispatchResult:
        user = await self._users.get_by_email(
            normalize_email(command.email)
        )

        if (
            user is None
            or not user.is_active
            or not user.email_verified
        ):
            return CodeDispatchResult(
                message=_PASSWORD_RESET_MESSAGE
            )

        now = datetime.now(UTC)

        purpose = VerificationPurpose.PASSWORD_RESET

        await self._codes.invalidate_active(
            user.id,
            purpose,
            now,
        )

        raw_code = self._code_service.generate()

        challenge_id = uuid4()

        challenge = VerificationCode(
            id=challenge_id,
            user_id=user.id,
            purpose=purpose,
            code_hash=self._code_service.digest(
                raw_code,
                challenge_id=challenge_id,
                user_id=user.id,
                purpose=purpose,
                created_at=now,
            ),
            expires_at=now + self._code_ttl,
            consumed_at=None,
            failed_attempts=0,
            created_at=now,
        )

        await self._codes.add(challenge)

        await self._transaction.commit()

        await self._email_service.send_verification_code(
            email=user.email,
            code=raw_code,
            purpose=purpose,
        )

        return CodeDispatchResult(
            message=_PASSWORD_RESET_MESSAGE,
            development_verification_code=(
                raw_code
                if self._expose_development_code
                else None
            ),
        )
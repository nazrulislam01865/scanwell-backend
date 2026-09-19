from datetime import UTC, datetime

from app.core.database.transaction import TransactionManager
from app.core.security.passwords import hash_password
from app.modules.auth.application.code_service import VerificationCodeService
from app.modules.auth.application.commands import ResetPasswordCommand
from app.modules.auth.domain.exceptions import (
    InvalidPasswordResetCodeError,
    PasswordResetAttemptsExceededError,
    PasswordResetCodeExpiredError,
)
from app.modules.auth.domain.repositories import (
    AuthSessionRepository,
    UserRepository,
    VerificationCodeRepository,
)
from app.modules.auth.domain.value_objects import VerificationPurpose, normalize_email


class ResetPassword:
    def __init__(
        self,
        *,
        users: UserRepository,
        codes: VerificationCodeRepository,
        sessions: AuthSessionRepository,
        transaction: TransactionManager,
        code_service: VerificationCodeService,
        max_attempts: int,
    ) -> None:
        self._users = users
        self._codes = codes
        self._sessions = sessions
        self._transaction = transaction
        self._code_service = code_service
        self._max_attempts = max_attempts

    async def execute(self, command: ResetPasswordCommand) -> None:
        user = await self._users.get_by_email(normalize_email(command.email))

        if user is None or not user.is_active or not user.email_verified:
            raise InvalidPasswordResetCodeError

        purpose = VerificationPurpose.PASSWORD_RESET
        challenge = await self._codes.get_latest_active(user.id, purpose)

        if challenge is None:
            raise InvalidPasswordResetCodeError
        if challenge.failed_attempts >= self._max_attempts:
            raise PasswordResetAttemptsExceededError

        now = datetime.now(UTC)
        if challenge.is_expired(now=now):
            challenge.consume(when=now)
            await self._codes.save(challenge)
            await self._transaction.commit()
            raise PasswordResetCodeExpiredError

        if not self._code_service.matches(
            command.code,
            challenge.code_hash,
            challenge_id=challenge.id,
            user_id=challenge.user_id,
            purpose=challenge.purpose,
            created_at=challenge.created_at,
        ):
            challenge.record_failed_attempt()
            await self._codes.save(challenge)
            await self._transaction.commit()

            if challenge.failed_attempts >= self._max_attempts:
                raise PasswordResetAttemptsExceededError

            raise InvalidPasswordResetCodeError

        challenge.consume(when=now)
        user.change_password_hash(
            hash_password(command.new_password),
            when=now,
        )

        await self._codes.save(challenge)
        await self._users.save(user)
        await self._sessions.revoke_all_for_user(
            user.id,
            revoked_at=now,
            reason="password_reset",
        )
        await self._transaction.commit()

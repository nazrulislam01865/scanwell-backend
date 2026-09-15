from datetime import UTC, datetime

from app.core.database.transaction import (
    TransactionManager,
)
from app.modules.auth.application.code_service import (
    VerificationCodeService,
)
from app.modules.auth.application.commands import (
    VerifyLoginOtpCommand,
)
from app.modules.auth.application.dto import (
    AuthResult,
    to_user_dto,
)
from app.modules.auth.domain.exceptions import (
    AccountDisabledError,
    EmailNotVerifiedError,
    InvalidVerificationCodeError,
    VerificationAttemptsExceededError,
    VerificationCodeExpiredError,
)
from app.modules.auth.domain.repositories import (
    TokenService,
    UserRepository,
    VerificationCodeRepository,
)
from app.modules.auth.domain.value_objects import (
    VerificationPurpose,
    normalize_email,
)


class VerifyLoginOtp:
    def __init__(
        self,
        *,
        users: UserRepository,
        codes: VerificationCodeRepository,
        transaction: TransactionManager,
        code_service: VerificationCodeService,
        token_service: TokenService,
        max_attempts: int,
    ) -> None:

        self._users = users
        self._codes = codes
        self._transaction = transaction

        self._code_service = (
            code_service
        )

        self._token_service = (
            token_service
        )

        self._max_attempts = (
            max_attempts
        )

    async def execute(
        self,
        command: VerifyLoginOtpCommand,
    ) -> AuthResult:

        user = await self._users.get_by_email(
            normalize_email(
                command.email
            )
        )

        if user is None:
            raise (
                InvalidVerificationCodeError
            )

        if not user.is_active:
            raise AccountDisabledError

        if not user.email_verified:
            raise EmailNotVerifiedError

        challenge = (
            await
            self._codes.get_latest_active(
                user.id,
                VerificationPurpose
                .LOGIN_OTP,
            )
        )

        if challenge is None:
            raise (
                InvalidVerificationCodeError
            )

        if (
            challenge.failed_attempts
            >= self._max_attempts
        ):
            raise (
                VerificationAttemptsExceededError
            )

        now = datetime.now(UTC)

        if challenge.is_expired(
            now=now
        ):

            challenge.consume(
                when=now
            )

            await self._codes.save(
                challenge
            )

            await (
                self._transaction.commit()
            )

            raise (
                VerificationCodeExpiredError
            )

        valid = (
            self._code_service.matches(
                command.code,
                challenge.code_hash,
                challenge_id=challenge.id,
                user_id=challenge.user_id,
                purpose=challenge.purpose,
                created_at=(
                    challenge.created_at
                ),
            )
        )

        if not valid:

            challenge.record_failed_attempt()

            await self._codes.save(
                challenge
            )

            await (
                self._transaction.commit()
            )

            if (
                challenge.failed_attempts
                >= self._max_attempts
            ):
                raise (
                    VerificationAttemptsExceededError
                )

            raise (
                InvalidVerificationCodeError
            )

        challenge.consume(
            when=now
        )

        await self._codes.save(
            challenge
        )

        await self._transaction.commit()

        return AuthResult(
            user=to_user_dto(user),
            tokens=(
                self._token_service
                .issue_pair(
                    user_id=user.id
                )
            ),
        )
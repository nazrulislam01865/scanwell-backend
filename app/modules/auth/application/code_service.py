import hashlib
import hmac
import secrets
from datetime import datetime
from uuid import UUID

from app.modules.auth.domain.value_objects import (
    VerificationPurpose,
)


class VerificationCodeService:
    def __init__(
        self,
        secret_key: str,
    ) -> None:
        self._secret = secret_key.encode(
            "utf-8"
        )

    def generate(self) -> str:
        return (
            f"{secrets.randbelow(1_000_000):06d}"
        )

    def digest(
        self,
        code: str,
        *,
        challenge_id: UUID,
        user_id: UUID,
        purpose: VerificationPurpose,
        created_at: datetime,
    ) -> str:

        created = created_at.isoformat(
            timespec="microseconds"
        )

        payload = "|".join(
            (
                str(challenge_id),
                str(user_id),
                purpose.value,
                created,
                code,
            )
        ).encode("utf-8")

        return hmac.new(
            self._secret,
            payload,
            hashlib.sha256,
        ).hexdigest()

    def matches(
        self,
        code: str,
        digest: str,
        *,
        challenge_id: UUID,
        user_id: UUID,
        purpose: VerificationPurpose,
        created_at: datetime,
    ) -> bool:

        return hmac.compare_digest(
            self.digest(
                code,
                challenge_id=challenge_id,
                user_id=user_id,
                purpose=purpose,
                created_at=created_at,
            ),
            digest,
        )
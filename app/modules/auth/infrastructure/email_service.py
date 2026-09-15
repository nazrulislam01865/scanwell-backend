from datetime import timedelta

from app.modules.auth.domain.exceptions import (
    EmailDeliveryFailedError,
)
from app.modules.auth.domain.value_objects import (
    VerificationPurpose,
)
from app.shared.application.email import (
    EmailMessage,
    EmailSender,
)
from app.shared.infrastructure.email.exceptions import (
    EmailDeliveryError,
)


class AuthEmailService:
    def __init__(
        self,
        *,
        sender: EmailSender,
        code_ttl: timedelta,
    ) -> None:
        self._sender = sender
        self._code_ttl = code_ttl

    async def send_verification_code(
        self,
        *,
        email: str,
        code: str,
        purpose: VerificationPurpose,
    ) -> None:

        minutes = max(
            1,
            int(
                self._code_ttl.total_seconds()
                // 60
            ),
        )

        expiry_text = (
            f"{minutes} minute"
            if minutes == 1
            else f"{minutes} minutes"
        )

        if (
            purpose
            is VerificationPurpose.EMAIL_VERIFICATION
        ):
            subject = (
                "Verify your ScanWell email"
            )

            heading = (
                "Verify your email address"
            )

            introduction = (
                "Use this verification code "
                "to finish creating your "
                "ScanWell account."
            )

        else:
            subject = (
                "Your ScanWell login code"
            )

            heading = "Sign in to ScanWell"

            introduction = (
                "Use this one-time code to "
                "sign in to your ScanWell "
                "account."
            )

        text_body = (
            f"{heading}\n\n"
            f"{introduction}\n\n"
            f"Your verification code is: "
            f"{code}\n\n"
            f"This code expires in "
            f"{expiry_text}.\n\n"
            "If you did not request this "
            "code, you can safely ignore "
            "this email."
        )

        html_body = f"""
<!doctype html>
<html lang="en">
<body
    style="
        font-family:Arial,sans-serif;
        line-height:1.5;
        color:#111827;
    "
>
    <div
        style="
            max-width:560px;
            margin:0 auto;
            padding:24px;
        "
    >
        <h1
            style="
                font-size:22px;
                margin:0 0 16px;
            "
        >
            {heading}
        </h1>

        <p>
            {introduction}
        </p>

        <div
            style="
                font-size:32px;
                font-weight:700;
                letter-spacing:8px;
                margin:24px 0;
            "
        >
            {code}
        </div>

        <p>
            This code expires in
            {expiry_text}.
        </p>

        <p
            style="
                color:#6b7280;
                font-size:14px;
            "
        >
            If you did not request this
            code, you can safely ignore
            this email.
        </p>
    </div>
</body>
</html>
"""

        try:
            await self._sender.send(
                EmailMessage(
                    to=email,
                    subject=subject,
                    text_body=text_body,
                    html_body=html_body,
                )
            )

        except EmailDeliveryError as exc:
            raise EmailDeliveryFailedError from exc
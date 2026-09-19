import httpx

from app.shared.application.email import EmailMessage
from app.shared.infrastructure.email.exceptions import (
    EmailDeliveryError,
)


class ResendEmailSender:
    API_URL = "https://api.resend.com/emails"

    def __init__(
        self,
        *,
        api_key: str,
        from_name: str,
        from_address: str,
        timeout_seconds: int,
    ) -> None:
        self._api_key = api_key
        self._from_name = from_name
        self._from_address = from_address
        self._timeout_seconds = timeout_seconds

    async def send(
        self,
        message: EmailMessage,
    ) -> None:
        payload: dict[str, object] = {
            "from": (
                f"{self._from_name} "
                f"<{self._from_address}>"
            ),
            "to": [message.to],
            "subject": message.subject,
            "text": message.text_body,
        }

        if message.html_body:
            payload["html"] = message.html_body

        if message.reply_to:
            payload["reply_to"] = message.reply_to

        try:
            async with httpx.AsyncClient(
                timeout=self._timeout_seconds,
            ) as client:
                response = await client.post(
                    self.API_URL,
                    headers={
                        "Authorization": (
                            f"Bearer {self._api_key}"
                        ),
                        "Content-Type": (
                            "application/json"
                        ),
                    },
                    json=payload,
                )

            response.raise_for_status()

        except httpx.HTTPError as exc:
            raise EmailDeliveryError(
                "Email delivery failed"
            ) from exc
import logging

import httpx

from app.shared.application.email import EmailMessage
from app.shared.infrastructure.email.exceptions import EmailDeliveryError

logger = logging.getLogger(__name__)


class BrevoEmailSender:
    API_URL = "https://api.brevo.com/v3/smtp/email"

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

    async def send(self, message: EmailMessage) -> None:
        payload: dict[str, object] = {
            "sender": {
                "name": self._from_name,
                "email": self._from_address,
            },
            "to": [{"email": message.to}],
            "subject": message.subject,
        }

        # Brevo expects one inline content type per request. Prefer HTML when
        # the application provides it and fall back to plain text otherwise.
        if message.html_body:
            payload["htmlContent"] = message.html_body
        else:
            payload["textContent"] = message.text_body

        if message.reply_to:
            payload["replyTo"] = {"email": message.reply_to}

        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                response = await client.post(
                    self.API_URL,
                    headers={
                        "accept": "application/json",
                        "api-key": self._api_key,
                        "content-type": "application/json",
                    },
                    json=payload,
                )

            response.raise_for_status()

        except httpx.HTTPStatusError as exc:
            logger.error(
                "Brevo rejected email. status=%s response=%s",
                exc.response.status_code,
                exc.response.text,
            )
            raise EmailDeliveryError("Email delivery failed") from exc

        except httpx.RequestError as exc:
            logger.exception("Could not connect to Brevo API")
            raise EmailDeliveryError("Email delivery failed") from exc

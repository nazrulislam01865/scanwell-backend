import asyncio
import base64
import logging
import time
from email.message import EmailMessage as MIMEEmailMessage
from email.utils import formataddr

import httpx

from app.shared.application.email import EmailMessage
from app.shared.infrastructure.email.exceptions import EmailDeliveryError

logger = logging.getLogger(__name__)


class GmailApiEmailSender:
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    SEND_URL = (
        "https://gmail.googleapis.com/"
        "gmail/v1/users/me/messages/send"
    )

    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        from_name: str,
        from_address: str,
        timeout_seconds: int,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._refresh_token = refresh_token
        self._from_name = from_name
        self._from_address = from_address
        self._timeout_seconds = timeout_seconds

        self._access_token: str | None = None
        self._access_token_expires_at = 0.0
        self._token_lock = asyncio.Lock()

    async def send(
        self,
        message: EmailMessage,
    ) -> None:
        access_token = await self._get_access_token()

        mime = MIMEEmailMessage()

        mime["Subject"] = message.subject

        mime["From"] = formataddr(
            (
                self._from_name,
                self._from_address,
            )
        )

        mime["To"] = message.to

        if message.reply_to:
            mime["Reply-To"] = message.reply_to

        mime.set_content(message.text_body)

        if message.html_body:
            mime.add_alternative(
                message.html_body,
                subtype="html",
            )

        raw_message = base64.urlsafe_b64encode(
            mime.as_bytes()
        ).decode("ascii")

        try:
            async with httpx.AsyncClient(
                timeout=self._timeout_seconds,
            ) as client:
                response = await client.post(
                    self.SEND_URL,
                    headers={
                        "Authorization": (
                            f"Bearer {access_token}"
                        ),
                        "Content-Type": "application/json",
                    },
                    json={
                        "raw": raw_message,
                    },
                )

            response.raise_for_status()

        except httpx.HTTPStatusError as exc:
            logger.error(
                "Gmail API rejected email. "
                "status=%s response=%s",
                exc.response.status_code,
                exc.response.text,
            )

            raise EmailDeliveryError(
                "Email delivery through Gmail API failed"
            ) from exc

        except httpx.RequestError as exc:
            logger.exception(
                "Could not connect to Gmail API"
            )

            raise EmailDeliveryError(
                "Email delivery through Gmail API failed"
            ) from exc

    async def _get_access_token(
        self,
    ) -> str:
        if (
            self._access_token
            and time.monotonic()
            < self._access_token_expires_at
        ):
            return self._access_token

        async with self._token_lock:
            if (
                self._access_token
                and time.monotonic()
                < self._access_token_expires_at
            ):
                return self._access_token

            try:
                async with httpx.AsyncClient(
                    timeout=self._timeout_seconds,
                ) as client:
                    response = await client.post(
                        self.TOKEN_URL,
                        data={
                            "client_id": (
                                self._client_id
                            ),
                            "client_secret": (
                                self._client_secret
                            ),
                            "refresh_token": (
                                self._refresh_token
                            ),
                            "grant_type": (
                                "refresh_token"
                            ),
                        },
                    )

                response.raise_for_status()

                payload = response.json()

                access_token = payload.get(
                    "access_token"
                )

                if not access_token:
                    raise EmailDeliveryError(
                        "Google did not return "
                        "an access token"
                    )

                expires_in = int(
                    payload.get(
                        "expires_in",
                        3600,
                    )
                )

                self._access_token = str(
                    access_token
                )

                self._access_token_expires_at = (
                    time.monotonic()
                    + max(
                        60,
                        expires_in - 60,
                    )
                )

                return self._access_token

            except httpx.HTTPStatusError as exc:
                logger.error(
                    "Google OAuth token refresh "
                    "failed. status=%s response=%s",
                    exc.response.status_code,
                    exc.response.text,
                )

                raise EmailDeliveryError(
                    "Could not authorize Gmail API"
                ) from exc

            except httpx.RequestError as exc:
                logger.exception(
                    "Could not connect to Google "
                    "OAuth token endpoint"
                )

                raise EmailDeliveryError(
                    "Could not authorize Gmail API"
                ) from exc
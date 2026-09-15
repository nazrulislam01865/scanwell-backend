import asyncio
import smtplib
from email.message import EmailMessage as MIMEEmailMessage
from email.utils import formataddr

from app.shared.application.email import EmailMessage
from app.shared.infrastructure.email.exceptions import EmailDeliveryError


class SMTPEmailSender:
    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str | None,
        password: str | None,
        from_name: str,
        from_address: str,
        use_tls: bool,
        use_ssl: bool,
        timeout_seconds: int,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._from_name = from_name
        self._from_address = from_address
        self._use_tls = use_tls
        self._use_ssl = use_ssl
        self._timeout_seconds = timeout_seconds

    async def send(self, message: EmailMessage) -> None:
        await asyncio.to_thread(self._send, message)

    def _send(self, message: EmailMessage) -> None:
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

        client_type = (
            smtplib.SMTP_SSL
            if self._use_ssl
            else smtplib.SMTP
        )

        try:
            with client_type(
                self._host,
                self._port,
                timeout=self._timeout_seconds,
            ) as smtp:

                if self._use_tls:
                    smtp.starttls()

                if self._username:
                    smtp.login(
                        self._username,
                        self._password or "",
                    )

                smtp.send_message(mime)

        except (
            OSError,
            smtplib.SMTPException,
        ) as exc:
            raise EmailDeliveryError(
                "Email delivery failed"
            ) from exc
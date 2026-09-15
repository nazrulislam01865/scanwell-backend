import logging

from app.shared.application.email import EmailMessage

logger = logging.getLogger(__name__)


class LoggingEmailSender:
    async def send(self, message: EmailMessage) -> None:
        logger.info(
            "Development email to=%s subject=%s body=%s",
            message.to,
            message.subject,
            message.text_body,
        )
from app.core.config.environment import Environment
from app.core.config.settings import Settings
from app.shared.application.email import EmailSender
from app.shared.infrastructure.email.exceptions import (
    EmailConfigurationError,
)
from app.shared.infrastructure.email.providers.logging import (
    LoggingEmailSender,
)
from app.shared.infrastructure.email.providers.smtp import (
    SMTPEmailSender,
)


def build_email_sender(
    settings: Settings,
) -> EmailSender:

    driver = settings.email_driver.strip().lower()

    if driver == "log":

        if settings.app_env is Environment.PRODUCTION:
            raise EmailConfigurationError(
                "EMAIL_DRIVER=log is not allowed in production"
            )

        return LoggingEmailSender()

    if driver != "smtp":
        raise EmailConfigurationError(
            f"Unsupported EMAIL_DRIVER: "
            f"{settings.email_driver}"
        )

    if not settings.smtp_host:
        raise EmailConfigurationError(
            "SMTP_HOST is required when "
            "EMAIL_DRIVER=smtp"
        )

    if (
        settings.smtp_use_tls
        and settings.smtp_use_ssl
    ):
        raise EmailConfigurationError(
            "SMTP_USE_TLS and SMTP_USE_SSL "
            "are mutually exclusive"
        )

    return SMTPEmailSender(
        host=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_username,
        password=settings.smtp_password,
        from_name=settings.email_from_name,
        from_address=settings.email_from_address,
        use_tls=settings.smtp_use_tls,
        use_ssl=settings.smtp_use_ssl,
        timeout_seconds=settings.smtp_timeout_seconds,
    )
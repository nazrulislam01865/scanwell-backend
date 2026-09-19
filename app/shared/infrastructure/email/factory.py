from app.core.config.environment import Environment
from app.core.config.settings import Settings
from app.shared.application.email import EmailSender
from app.shared.infrastructure.email.exceptions import (
    EmailConfigurationError,
)
from app.shared.infrastructure.email.providers.brevo import BrevoEmailSender
from app.shared.infrastructure.email.providers.gmail_api import (
    GmailApiEmailSender,
)
from app.shared.infrastructure.email.providers.logging import (
    LoggingEmailSender,
)
from app.shared.infrastructure.email.providers.resend import (
    ResendEmailSender,
)
from app.shared.infrastructure.email.providers.smtp import (
    SMTPEmailSender,
)


def build_email_sender(
    settings: Settings,
) -> EmailSender:

    driver = settings.email_driver.strip().lower()

    # --------------------------------
    # Development logging provider
    # --------------------------------
    if driver == "log":

        if settings.app_env is Environment.PRODUCTION:
            raise EmailConfigurationError(
                "EMAIL_DRIVER=log is not allowed in production"
            )

        return LoggingEmailSender()

    # --------------------------------
    # Gmail API provider
    # --------------------------------
    if driver == "gmail_api":

        if not settings.gmail_client_id:
            raise EmailConfigurationError(
                "GMAIL_CLIENT_ID is required when "
                "EMAIL_DRIVER=gmail_api"
            )

        if not settings.gmail_client_secret:
            raise EmailConfigurationError(
                "GMAIL_CLIENT_SECRET is required when "
                "EMAIL_DRIVER=gmail_api"
            )

        if not settings.gmail_refresh_token:
            raise EmailConfigurationError(
                "GMAIL_REFRESH_TOKEN is required when "
                "EMAIL_DRIVER=gmail_api"
            )

        return GmailApiEmailSender(
            client_id=settings.gmail_client_id,
            client_secret=settings.gmail_client_secret,
            refresh_token=settings.gmail_refresh_token,
            from_name=settings.email_from_name,
            from_address=settings.email_from_address,
            timeout_seconds=settings.gmail_timeout_seconds,
        )

    # --------------------------------
    # Brevo HTTP API provider
    # --------------------------------
    if driver == "brevo":
        if not settings.brevo_api_key:
            raise EmailConfigurationError(
                "BREVO_API_KEY is required when "
                "EMAIL_DRIVER=brevo"
            )

        from_address = settings.email_from_address.strip()
        if (
            not from_address
            or "@" not in from_address
            or from_address == "no-reply@scanwell.local"
        ):
            raise EmailConfigurationError(
                "EMAIL_FROM_ADDRESS must be a verified Brevo sender "
                "when EMAIL_DRIVER=brevo"
            )

        return BrevoEmailSender(
            api_key=settings.brevo_api_key,
            from_name=settings.email_from_name,
            from_address=from_address,
            timeout_seconds=settings.brevo_timeout_seconds,
        )

    # --------------------------------
    # Resend provider
    # --------------------------------
    if driver == "resend":

        if not settings.resend_api_key:
            raise EmailConfigurationError(
                "RESEND_API_KEY is required when "
                "EMAIL_DRIVER=resend"
            )

        return ResendEmailSender(
            api_key=settings.resend_api_key,
            from_name=settings.email_from_name,
            from_address=settings.email_from_address,
            timeout_seconds=settings.resend_timeout_seconds,
        )

    # --------------------------------
    # SMTP provider
    # --------------------------------
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
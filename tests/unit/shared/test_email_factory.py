import pytest

from app.core.config.environment import Environment
from app.core.config.settings import Settings
from app.shared.infrastructure.email.exceptions import EmailConfigurationError
from app.shared.infrastructure.email.factory import build_email_sender
from app.shared.infrastructure.email.providers.brevo import BrevoEmailSender


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "app_env": Environment.PRODUCTION,
        "email_driver": "brevo",
        "brevo_api_key": "xkeysib-test",
        "email_from_address": "sender@gmail.com",
        "email_from_name": "ScanWell",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_factory_builds_brevo_sender() -> None:
    sender = build_email_sender(_settings())
    assert isinstance(sender, BrevoEmailSender)


def test_factory_requires_brevo_api_key() -> None:
    with pytest.raises(EmailConfigurationError, match="BREVO_API_KEY"):
        build_email_sender(_settings(brevo_api_key=None))


def test_factory_requires_verified_sender_address() -> None:
    with pytest.raises(EmailConfigurationError, match="verified Brevo sender"):
        build_email_sender(_settings(email_from_address="no-reply@scanwell.local"))

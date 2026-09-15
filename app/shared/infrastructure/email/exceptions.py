class EmailError(Exception):
    """Base exception for centralized email delivery."""


class EmailConfigurationError(EmailError):
    """Raised when the selected email provider is misconfigured."""


class EmailDeliveryError(EmailError):
    """Raised when a configured provider cannot deliver a message."""
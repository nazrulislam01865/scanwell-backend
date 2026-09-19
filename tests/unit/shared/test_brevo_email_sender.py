from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.shared.application.email import EmailMessage
from app.shared.infrastructure.email.exceptions import EmailDeliveryError
from app.shared.infrastructure.email.providers.brevo import BrevoEmailSender


class _AsyncClientContext:
    def __init__(self, client: AsyncMock) -> None:
        self._client = client

    async def __aenter__(self) -> AsyncMock:
        return self._client

    async def __aexit__(self, *_args: object) -> None:
        return None


def _sender() -> BrevoEmailSender:
    return BrevoEmailSender(
        api_key="xkeysib-test",
        from_name="ScanWell",
        from_address="sender@gmail.com",
        timeout_seconds=15,
    )


@pytest.mark.asyncio
async def test_sends_html_email_through_brevo_api() -> None:
    request = httpx.Request("POST", BrevoEmailSender.API_URL)
    response = httpx.Response(201, json={"messageId": "test-id"}, request=request)
    client = AsyncMock()
    client.post.return_value = response

    with patch(
        "app.shared.infrastructure.email.providers.brevo.httpx.AsyncClient",
        return_value=_AsyncClientContext(client),
    ):
        await _sender().send(
            EmailMessage(
                to="user@example.com",
                subject="Verify your email",
                text_body="Code: 123456",
                html_body="<p>Code: 123456</p>",
                reply_to="support@example.com",
            )
        )

    client.post.assert_awaited_once()
    _, kwargs = client.post.await_args
    assert kwargs["headers"]["api-key"] == "xkeysib-test"
    assert kwargs["json"] == {
        "sender": {"name": "ScanWell", "email": "sender@gmail.com"},
        "to": [{"email": "user@example.com"}],
        "subject": "Verify your email",
        "htmlContent": "<p>Code: 123456</p>",
        "replyTo": {"email": "support@example.com"},
    }


@pytest.mark.asyncio
async def test_uses_text_content_when_html_is_absent() -> None:
    request = httpx.Request("POST", BrevoEmailSender.API_URL)
    response = httpx.Response(201, json={"messageId": "test-id"}, request=request)
    client = AsyncMock()
    client.post.return_value = response

    with patch(
        "app.shared.infrastructure.email.providers.brevo.httpx.AsyncClient",
        return_value=_AsyncClientContext(client),
    ):
        await _sender().send(
            EmailMessage(
                to="user@example.com",
                subject="Login code",
                text_body="Code: 123456",
            )
        )

    _, kwargs = client.post.await_args
    assert kwargs["json"]["textContent"] == "Code: 123456"
    assert "htmlContent" not in kwargs["json"]


@pytest.mark.asyncio
async def test_converts_brevo_http_error_to_email_delivery_error() -> None:
    request = httpx.Request("POST", BrevoEmailSender.API_URL)
    response = httpx.Response(401, json={"message": "unauthorized"}, request=request)
    client = AsyncMock()
    client.post.return_value = response

    with (
        patch(
            "app.shared.infrastructure.email.providers.brevo.httpx.AsyncClient",
            return_value=_AsyncClientContext(client),
        ),
        pytest.raises(EmailDeliveryError),
    ):
        await _sender().send(
            EmailMessage(
                to="user@example.com",
                subject="Test",
                text_body="Test",
            )
        )

from datetime import timedelta
from uuid import uuid4

import pytest

from app.core.security.jwt import InvalidTokenError, JWTService


def build_service() -> JWTService:
    return JWTService(
        secret_key="test-secret-key-with-enough-entropy",
        algorithm="HS256",
        issuer="scanwell-test",
        audience="scanwell-mobile",
        access_token_ttl=timedelta(minutes=15),
        refresh_token_ttl=timedelta(days=30),
    )


def test_access_token_round_trip_contains_expected_claims() -> None:
    user_id = uuid4()
    service = build_service()

    token = service.create_access_token(user_id=user_id)
    claims = service.decode(token, expected_type="access")

    assert claims.subject == user_id
    assert claims.token_type == "access"
    assert claims.jti


def test_refresh_token_rejected_when_access_token_expected() -> None:
    service = build_service()
    token = service.create_refresh_token(user_id=uuid4())

    with pytest.raises(InvalidTokenError):
        service.decode(token, expected_type="access")

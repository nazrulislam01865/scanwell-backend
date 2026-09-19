from datetime import timedelta
from uuid import uuid4

import pytest

from app.core.security.jwt import JWTService
from app.modules.auth.domain.exceptions import InvalidAuthTokenError
from app.modules.auth.infrastructure.token_service import AuthTokenService


def build_token_service() -> AuthTokenService:
    return AuthTokenService(
        jwt_service=JWTService(
            secret_key="test-secret-key-with-enough-entropy",
            algorithm="HS256",
            issuer="scanwell-test",
            audience="scanwell-mobile",
            access_token_ttl=timedelta(minutes=15),
            refresh_token_ttl=timedelta(days=30),
        ),
        access_expires_in=900,
    )


def test_refresh_token_contains_session_identity_and_hashes_securely() -> None:
    service = build_token_service()
    user_id = uuid4()
    session_id = uuid4()

    tokens = service.issue_pair(user_id=user_id, session_id=session_id)
    identity = service.refresh_identity(tokens.refresh_token)
    digest = service.hash_refresh_token(tokens.refresh_token)

    assert identity.user_id == user_id
    assert identity.session_id == session_id
    assert len(digest) == 64
    assert digest != tokens.refresh_token
    assert service.refresh_token_matches(tokens.refresh_token, digest)


def test_legacy_refresh_token_without_session_id_is_not_accepted_for_session_refresh() -> None:
    jwt_service = JWTService(
        secret_key="test-secret-key-with-enough-entropy",
        algorithm="HS256",
        issuer="scanwell-test",
        audience="scanwell-mobile",
        access_token_ttl=timedelta(minutes=15),
        refresh_token_ttl=timedelta(days=30),
    )
    service = AuthTokenService(jwt_service=jwt_service, access_expires_in=900)
    legacy_refresh = jwt_service.create_refresh_token(user_id=uuid4())

    with pytest.raises(InvalidAuthTokenError):
        service.refresh_identity(legacy_refresh)

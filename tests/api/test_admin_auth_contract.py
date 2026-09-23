from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.application.admin_dto import AdminAuthResult, AdminDTO
from app.modules.auth.domain.exceptions import InvalidAuthTokenError
from app.modules.auth.domain.value_objects import AuthTokens
from app.modules.auth.presentation.admin_dependencies import (
    get_admin_login_use_case,
    get_admin_logout_use_case,
    get_admin_refresh_use_case,
    get_admin_token_service,
    get_current_admin,
)
from app.modules.auth.presentation.dependencies import get_auth_token_service


class StubUseCase:
    def __init__(self, result=None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.commands = []

    async def execute(self, command):
        self.commands.append(command)
        if self.error:
            raise self.error
        return self.result


def admin_dto() -> AdminDTO:
    return AdminDTO(
        id=uuid4(),
        name="ScanWell Admin",
        email="admin@scanwell.app",
        role="Super Admin",
        status="Active",
        last_login_at=datetime.now(UTC),
    )


def token_pair() -> AuthTokens:
    return AuthTokens(
        access_token="admin-access-token",
        refresh_token="admin-refresh-token",
        expires_in=900,
    )


def test_admin_login_contract() -> None:
    admin = admin_dto()
    stub = StubUseCase(AdminAuthResult(admin=admin, tokens=token_pair()))
    app.dependency_overrides[get_admin_login_use_case] = lambda: stub
    try:
        response = TestClient(app).post(
            "/api/v1/admin/auth/login",
            json={"email": admin.email, "password": "secret123"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["admin"]["id"] == str(admin.id)
    assert body["admin"]["role"] == "Super Admin"
    assert body["access_token"] == "admin-access-token"
    assert body["refresh_token"] == "admin-refresh-token"
    assert stub.commands[0].email == admin.email


def test_admin_refresh_contract() -> None:
    tokens = token_pair()
    stub = StubUseCase(tokens)
    app.dependency_overrides[get_admin_refresh_use_case] = lambda: stub
    try:
        response = TestClient(app).post(
            "/api/v1/admin/auth/refresh",
            json={"refresh_token": "old-refresh-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["access_token"] == tokens.access_token
    assert stub.commands[0].refresh_token == "old-refresh-token"


def test_admin_logout_contract() -> None:
    stub = StubUseCase()
    app.dependency_overrides[get_admin_logout_use_case] = lambda: stub
    try:
        response = TestClient(app).post(
            "/api/v1/admin/auth/logout",
            json={"refresh_token": "admin-refresh-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"message": "Logged out successfully."}
    assert stub.commands[0].refresh_token == "admin-refresh-token"


def test_admin_me_contract() -> None:
    admin = admin_dto()
    app.dependency_overrides[get_current_admin] = lambda: admin
    try:
        response = TestClient(app).get(
            "/api/v1/admin/auth/me",
            headers={"Authorization": "Bearer admin-access-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["email"] == admin.email
    assert response.json()["status"] == "Active"


def test_openapi_exposes_only_requested_admin_auth_surface() -> None:
    paths = app.openapi()["paths"]
    expected = {
        "/api/v1/admin/auth/login": "post",
        "/api/v1/admin/auth/refresh": "post",
        "/api/v1/admin/auth/logout": "post",
        "/api/v1/admin/auth/me": "get",
    }
    for path, method in expected.items():
        assert method in paths[path]


def test_mobile_access_token_is_not_valid_as_admin_token() -> None:
    user_id = uuid4()
    session_id = uuid4()
    mobile_token = get_auth_token_service().issue_pair(
        user_id=user_id,
        session_id=session_id,
    ).access_token

    with pytest.raises(InvalidAuthTokenError):
        get_admin_token_service().access_identity(mobile_token)

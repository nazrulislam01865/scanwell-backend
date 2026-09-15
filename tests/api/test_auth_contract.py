from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.application.dto import AuthUserDTO, RegistrationResult
from app.modules.auth.domain.exceptions import InvalidCredentialsError
from app.modules.auth.domain.value_objects import LoginMethod
from app.modules.auth.presentation.dependencies import (
    get_current_user_id,
    get_get_current_user_use_case,
    get_login_user_use_case,
    get_register_user_use_case,
)


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


def user_dto() -> AuthUserDTO:
    return AuthUserDTO(
        id=uuid4(),
        name="Nazrul Islam",
        email="nazrul@example.com",
        phone="+8801712345678",
        preferred_login_method=LoginMethod.PASSWORD,
        email_verified=False,
        is_active=True,
    )


def test_register_contract_matches_flutter_signup_fields() -> None:
    stub = StubUseCase(
        RegistrationResult(
            user=user_dto(),
            verification_required=True,
            development_verification_code="123456",
        )
    )
    app.dependency_overrides[get_register_user_use_case] = lambda: stub
    try:
        response = TestClient(app).post(
            "/api/v1/auth/register",
            json={
                "name": "Nazrul Islam",
                "email": "nazrul@example.com",
                "phone": "+8801712345678",
                "password": "secret123",
                "preferred_login_method": "password",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert body["verification_required"] is True
    assert body["development_verification_code"] == "123456"
    assert body["user"]["email"] == "nazrul@example.com"
    assert stub.commands[0].phone == "+8801712345678"


def test_password_login_returns_stable_error_payload() -> None:
    stub = StubUseCase(error=InvalidCredentialsError())
    app.dependency_overrides[get_login_user_use_case] = lambda: stub
    try:
        response = TestClient(app).post(
            "/api/v1/auth/login",
            json={"email": "nazrul@example.com", "password": "wrong-password"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json() == {
        "detail": {
            "code": "INVALID_CREDENTIALS",
            "message": "Email or password is incorrect.",
        }
    }


def test_me_returns_authenticated_user() -> None:
    user = user_dto()
    verified_user = AuthUserDTO(
        id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        preferred_login_method=user.preferred_login_method,
        email_verified=True,
        is_active=True,
    )
    stub = StubUseCase(verified_user)
    app.dependency_overrides[get_current_user_id] = lambda: user.id
    app.dependency_overrides[get_get_current_user_use_case] = lambda: stub
    try:
        response = TestClient(app).get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer test-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["id"] == str(user.id)
    assert response.json()["email_verified"] is True


def test_openapi_exposes_complete_auth_surface() -> None:
    paths = app.openapi()["paths"]
    expected = {
        "/api/v1/auth/register": "post",
        "/api/v1/auth/verify-email": "post",
        "/api/v1/auth/resend-verification": "post",
        "/api/v1/auth/login": "post",
        "/api/v1/auth/login/otp/request": "post",
        "/api/v1/auth/login/otp/verify": "post",
        "/api/v1/auth/refresh": "post",
        "/api/v1/auth/me": "get",
    }
    for path, method in expected.items():
        assert method in paths[path]

from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.presentation.dependencies import get_current_user_id
from app.modules.users.application.dto import (
    PersonalDataExportDTO,
    UserPreferencesDTO,
    UserProfileDTO,
)
from app.modules.users.presentation.dependencies import (
    get_delete_account_use_case,
    get_export_personal_data_use_case,
    get_preferences_use_case,
    get_profile_use_case,
    get_update_name_use_case,
    get_update_phone_use_case,
    get_update_preferences_use_case,
    get_update_profile_use_case,
)


class StubUseCase:
    def __init__(self, result=None) -> None:
        self.result = result
        self.commands = []

    async def execute(self, command):
        self.commands.append(command)
        return self.result


def profile_dto() -> UserProfileDTO:
    now = datetime.now(UTC)
    return UserProfileDTO(
        id=uuid4(),
        name="Nazrul Islam",
        email="nazrul@example.com",
        phone="+8801712345678",
        preferred_login_method="password",
        email_verified=True,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def preferences_dto() -> UserPreferencesDTO:
    return UserPreferencesDTO(
        email_notifications=True,
        push_notifications=True,
        preferred_login_method="password",
    )


def test_get_profile_contract() -> None:
    profile = profile_dto()
    stub = StubUseCase(profile)
    app.dependency_overrides[get_current_user_id] = lambda: profile.id
    app.dependency_overrides[get_profile_use_case] = lambda: stub
    try:
        response = TestClient(app).get("/api/v1/users/me")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["email"] == "nazrul@example.com"


def test_update_profile_contract_allows_phone_removal() -> None:
    profile = profile_dto()
    profile = UserProfileDTO(
        id=profile.id,
        name="Updated Name",
        email=profile.email,
        phone=None,
        preferred_login_method=profile.preferred_login_method,
        email_verified=profile.email_verified,
        is_active=profile.is_active,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )
    stub = StubUseCase(profile)
    app.dependency_overrides[get_current_user_id] = lambda: profile.id
    app.dependency_overrides[get_update_profile_use_case] = lambda: stub
    try:
        response = TestClient(app).patch(
            "/api/v1/users/me",
            json={"name": "Updated Name", "phone": None},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert stub.commands[0].update_phone is True
    assert response.json()["phone"] is None


def test_preferences_contract() -> None:
    profile = profile_dto()
    stub = StubUseCase(preferences_dto())
    app.dependency_overrides[get_current_user_id] = lambda: profile.id
    app.dependency_overrides[get_preferences_use_case] = lambda: stub
    try:
        response = TestClient(app).get("/api/v1/users/me/preferences")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["preferred_login_method"] == "password"


def test_export_contract() -> None:
    profile = profile_dto()
    result = PersonalDataExportDTO(
        exported_at=datetime.now(UTC),
        profile=profile,
        preferences=preferences_dto(),
    )
    stub = StubUseCase(result)
    app.dependency_overrides[get_current_user_id] = lambda: profile.id
    app.dependency_overrides[get_export_personal_data_use_case] = lambda: stub
    try:
        response = TestClient(app).get("/api/v1/users/me/export")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["profile"]["id"] == str(profile.id)


def test_delete_account_contract_requires_password() -> None:
    profile = profile_dto()
    stub = StubUseCase()
    app.dependency_overrides[get_current_user_id] = lambda: profile.id
    app.dependency_overrides[get_delete_account_use_case] = lambda: stub
    try:
        response = TestClient(app).request(
            "DELETE",
            "/api/v1/users/me",
            json={"password": "secret123"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"message": "Account deleted successfully."}
    assert stub.commands[0].password == "secret123"


def test_openapi_exposes_complete_users_surface() -> None:
    paths = app.openapi()["paths"]
    expected = {
        "/api/v1/users/me": {"get", "patch", "delete"},
        "/api/v1/users/me/name": {"patch"},
        "/api/v1/users/me/phone": {"patch"},
        "/api/v1/users/me/preferences": {"get", "patch"},
        "/api/v1/users/me/export": {"get"},
    }
    for path, methods in expected.items():
        assert methods.issubset(paths[path])

    assert get_update_name_use_case
    assert get_update_phone_use_case
    assert get_update_preferences_use_case

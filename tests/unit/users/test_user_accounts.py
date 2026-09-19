from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.core.security.passwords import hash_password
from app.modules.users.application.commands import (
    DeleteAccountCommand,
    UpdateNameCommand,
    UpdatePhoneCommand,
    UpdatePreferencesCommand,
    UpdateProfileCommand,
)
from app.modules.users.application.queries import (
    ExportPersonalDataQuery,
    GetPreferencesQuery,
    GetProfileQuery,
)
from app.modules.users.application.use_cases.delete_account import DeleteAccount
from app.modules.users.application.use_cases.export_personal_data import ExportPersonalData
from app.modules.users.application.use_cases.get_preferences import GetPreferences
from app.modules.users.application.use_cases.get_profile import GetProfile
from app.modules.users.application.use_cases.update_name import UpdateName
from app.modules.users.application.use_cases.update_phone import UpdatePhone
from app.modules.users.application.use_cases.update_preferences import UpdatePreferences
from app.modules.users.application.use_cases.update_profile import UpdateProfile
from app.modules.users.domain.entities import UserAccount, UserPreferences
from app.modules.users.domain.exceptions import InvalidAccountPasswordError
from tests.unit.users.fakes import (
    FakeTransaction,
    InMemoryUserAccountRepository,
    InMemoryUserPreferencesRepository,
    InMemoryUserSecurityRepository,
)


def make_user() -> UserAccount:
    now = datetime.now(UTC)
    return UserAccount(
        id=uuid4(),
        name="Nazrul Islam",
        email="nazrul@example.com",
        phone="+8801712345678",
        password_hash=hash_password("secret123"),
        preferred_login_method="password",
        email_verified_at=now,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_get_profile_returns_current_account() -> None:
    users = InMemoryUserAccountRepository()
    user = make_user()
    users.items[user.id] = user

    result = await GetProfile(users=users).execute(GetProfileQuery(user_id=user.id))

    assert result.id == user.id
    assert result.email == "nazrul@example.com"
    assert result.email_verified is True


@pytest.mark.asyncio
async def test_update_profile_changes_name_and_can_clear_phone() -> None:
    users = InMemoryUserAccountRepository()
    transaction = FakeTransaction()
    user = make_user()
    users.items[user.id] = user

    result = await UpdateProfile(users=users, transaction=transaction).execute(
        UpdateProfileCommand(
            user_id=user.id,
            name="  Nazrul I.  ",
            phone=None,
            update_phone=True,
        )
    )

    assert result.name == "Nazrul I."
    assert result.phone is None
    assert transaction.commits == 1


@pytest.mark.asyncio
async def test_update_name_and_phone_are_independently_supported() -> None:
    users = InMemoryUserAccountRepository()
    transaction = FakeTransaction()
    user = make_user()
    users.items[user.id] = user

    name_result = await UpdateName(users=users, transaction=transaction).execute(
        UpdateNameCommand(user_id=user.id, name="New Name")
    )
    phone_result = await UpdatePhone(users=users, transaction=transaction).execute(
        UpdatePhoneCommand(user_id=user.id, phone="+8801800000000")
    )

    assert name_result.name == "New Name"
    assert phone_result.phone == "+8801800000000"
    assert transaction.commits == 2


@pytest.mark.asyncio
async def test_preferences_return_defaults_and_can_be_persisted() -> None:
    users = InMemoryUserAccountRepository()
    preferences = InMemoryUserPreferencesRepository()
    transaction = FakeTransaction()
    user = make_user()
    users.items[user.id] = user

    defaults = await GetPreferences(users=users, preferences=preferences).execute(
        GetPreferencesQuery(user_id=user.id)
    )
    assert defaults.email_notifications is True
    assert defaults.push_notifications is True
    assert defaults.preferred_login_method == "password"

    updated = await UpdatePreferences(
        users=users,
        preferences=preferences,
        transaction=transaction,
    ).execute(
        UpdatePreferencesCommand(
            user_id=user.id,
            email_notifications=False,
            preferred_login_method="otp",
        )
    )

    assert updated.email_notifications is False
    assert updated.push_notifications is True
    assert updated.preferred_login_method == "otp"
    assert preferences.items[user.id].email_notifications is False
    assert users.items[user.id].preferred_login_method == "otp"


@pytest.mark.asyncio
async def test_export_contains_only_current_account_and_preferences() -> None:
    users = InMemoryUserAccountRepository()
    preferences = InMemoryUserPreferencesRepository()
    user = make_user()
    users.items[user.id] = user
    preferences.items[user.id] = UserPreferences(
        user_id=user.id,
        email_notifications=False,
        push_notifications=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    result = await ExportPersonalData(users=users, preferences=preferences).execute(
        ExportPersonalDataQuery(user_id=user.id)
    )

    assert result.profile.email == user.email
    assert result.preferences.email_notifications is False
    assert result.preferences.push_notifications is True


@pytest.mark.asyncio
async def test_delete_account_requires_current_password() -> None:
    users = InMemoryUserAccountRepository()
    preferences = InMemoryUserPreferencesRepository()
    security = InMemoryUserSecurityRepository()
    transaction = FakeTransaction()
    user = make_user()
    users.items[user.id] = user

    with pytest.raises(InvalidAccountPasswordError):
        await DeleteAccount(
            users=users,
            preferences=preferences,
            security=security,
            transaction=transaction,
        ).execute(DeleteAccountCommand(user_id=user.id, password="wrongpass"))

    assert user.is_active is True
    assert transaction.commits == 0


@pytest.mark.asyncio
async def test_delete_account_anonymizes_and_revokes_security_state() -> None:
    users = InMemoryUserAccountRepository()
    preferences = InMemoryUserPreferencesRepository()
    security = InMemoryUserSecurityRepository()
    transaction = FakeTransaction()
    user = make_user()
    users.items[user.id] = user
    preferences.items[user.id] = UserPreferences(
        user_id=user.id,
        email_notifications=True,
        push_notifications=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    await DeleteAccount(
        users=users,
        preferences=preferences,
        security=security,
        transaction=transaction,
    ).execute(DeleteAccountCommand(user_id=user.id, password="secret123"))

    assert user.is_active is False
    assert user.deleted_at is not None
    assert user.name == "Deleted User"
    assert user.phone is None
    assert user.email.startswith("deleted+")
    assert user.id in preferences.deleted_ids
    assert security.revocations[0][2] == "account_deleted"
    assert security.invalidations[0][0] == user.id
    assert transaction.commits == 1

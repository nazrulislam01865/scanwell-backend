from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.core.database.transaction import SQLAlchemyTransaction
from app.modules.users.application.use_cases.delete_account import DeleteAccount
from app.modules.users.application.use_cases.export_personal_data import ExportPersonalData
from app.modules.users.application.use_cases.get_preferences import GetPreferences
from app.modules.users.application.use_cases.get_profile import GetProfile
from app.modules.users.application.use_cases.update_name import UpdateName
from app.modules.users.application.use_cases.update_phone import UpdatePhone
from app.modules.users.application.use_cases.update_preferences import UpdatePreferences
from app.modules.users.application.use_cases.update_profile import UpdateProfile
from app.modules.users.infrastructure.repository import (
    SQLAlchemyUserAccountRepository,
    SQLAlchemyUserPreferencesRepository,
    SQLAlchemyUserSecurityRepository,
)


def _repositories(
    session: AsyncSession,
) -> tuple[SQLAlchemyUserAccountRepository, SQLAlchemyUserPreferencesRepository]:
    return (
        SQLAlchemyUserAccountRepository(session),
        SQLAlchemyUserPreferencesRepository(session),
    )


async def get_profile_use_case(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> GetProfile:
    users, _preferences = _repositories(session)
    return GetProfile(users=users)


async def get_update_profile_use_case(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UpdateProfile:
    users, _preferences = _repositories(session)
    return UpdateProfile(users=users, transaction=SQLAlchemyTransaction(session))


async def get_update_name_use_case(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UpdateName:
    users, _preferences = _repositories(session)
    return UpdateName(users=users, transaction=SQLAlchemyTransaction(session))


async def get_update_phone_use_case(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UpdatePhone:
    users, _preferences = _repositories(session)
    return UpdatePhone(users=users, transaction=SQLAlchemyTransaction(session))


async def get_preferences_use_case(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> GetPreferences:
    users, preferences = _repositories(session)
    return GetPreferences(users=users, preferences=preferences)


async def get_update_preferences_use_case(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UpdatePreferences:
    users, preferences = _repositories(session)
    return UpdatePreferences(
        users=users,
        preferences=preferences,
        transaction=SQLAlchemyTransaction(session),
    )


async def get_export_personal_data_use_case(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ExportPersonalData:
    users, preferences = _repositories(session)
    return ExportPersonalData(users=users, preferences=preferences)


async def get_delete_account_use_case(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> DeleteAccount:
    users, preferences = _repositories(session)
    return DeleteAccount(
        users=users,
        preferences=preferences,
        security=SQLAlchemyUserSecurityRepository(session),
        transaction=SQLAlchemyTransaction(session),
    )

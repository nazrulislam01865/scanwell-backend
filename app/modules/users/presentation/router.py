from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.modules.auth.presentation.dependencies import get_current_user_id
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
from app.modules.users.presentation.schemas import (
    DeleteAccountRequest,
    MessageResponse,
    PersonalDataExportResponse,
    UpdateNameRequest,
    UpdatePhoneRequest,
    UpdatePreferencesRequest,
    UpdateProfileRequest,
    UserPreferencesResponse,
    UserProfileResponse,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserProfileResponse)
async def get_profile(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    use_case: Annotated[GetProfile, Depends(get_profile_use_case)],
) -> UserProfileResponse:
    profile = await use_case.execute(GetProfileQuery(user_id=user_id))
    return UserProfileResponse.from_dto(profile)


@router.patch("/me", response_model=UserProfileResponse)
async def update_profile(
    payload: UpdateProfileRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    use_case: Annotated[UpdateProfile, Depends(get_update_profile_use_case)],
) -> UserProfileResponse:
    profile = await use_case.execute(
        UpdateProfileCommand(
            user_id=user_id,
            name=payload.name,
            phone=payload.phone,
            update_phone="phone" in payload.model_fields_set,
        )
    )
    return UserProfileResponse.from_dto(profile)


@router.patch("/me/name", response_model=UserProfileResponse)
async def update_name(
    payload: UpdateNameRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    use_case: Annotated[UpdateName, Depends(get_update_name_use_case)],
) -> UserProfileResponse:
    profile = await use_case.execute(UpdateNameCommand(user_id=user_id, name=payload.name))
    return UserProfileResponse.from_dto(profile)


@router.patch("/me/phone", response_model=UserProfileResponse)
async def update_phone(
    payload: UpdatePhoneRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    use_case: Annotated[UpdatePhone, Depends(get_update_phone_use_case)],
) -> UserProfileResponse:
    profile = await use_case.execute(UpdatePhoneCommand(user_id=user_id, phone=payload.phone))
    return UserProfileResponse.from_dto(profile)


@router.get("/me/preferences", response_model=UserPreferencesResponse)
async def get_preferences(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    use_case: Annotated[GetPreferences, Depends(get_preferences_use_case)],
) -> UserPreferencesResponse:
    preferences = await use_case.execute(GetPreferencesQuery(user_id=user_id))
    return UserPreferencesResponse.from_dto(preferences)


@router.patch("/me/preferences", response_model=UserPreferencesResponse)
async def update_preferences(
    payload: UpdatePreferencesRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    use_case: Annotated[UpdatePreferences, Depends(get_update_preferences_use_case)],
) -> UserPreferencesResponse:
    preferences = await use_case.execute(
        UpdatePreferencesCommand(
            user_id=user_id,
            email_notifications=payload.email_notifications,
            push_notifications=payload.push_notifications,
            preferred_login_method=(
                payload.preferred_login_method.value
                if payload.preferred_login_method is not None
                else None
            ),
        )
    )
    return UserPreferencesResponse.from_dto(preferences)


@router.get("/me/export", response_model=PersonalDataExportResponse)
async def export_personal_data(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    use_case: Annotated[ExportPersonalData, Depends(get_export_personal_data_use_case)],
) -> PersonalDataExportResponse:
    data = await use_case.execute(ExportPersonalDataQuery(user_id=user_id))
    return PersonalDataExportResponse.from_dto(data)


@router.delete("/me", response_model=MessageResponse)
async def delete_account(
    payload: DeleteAccountRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    use_case: Annotated[DeleteAccount, Depends(get_delete_account_use_case)],
) -> MessageResponse:
    await use_case.execute(DeleteAccountCommand(user_id=user_id, password=payload.password))
    return MessageResponse(message="Account deleted successfully.")

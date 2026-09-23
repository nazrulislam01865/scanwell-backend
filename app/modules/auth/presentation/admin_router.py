from typing import Annotated

from fastapi import APIRouter, Depends

from app.modules.auth.application.admin_dto import AdminDTO
from app.modules.auth.application.commands import (
    LoginUserCommand,
    LogoutUserCommand,
    RefreshTokenCommand,
)
from app.modules.auth.application.use_cases.login_admin import LoginAdmin
from app.modules.auth.application.use_cases.logout_user import LogoutUser
from app.modules.auth.application.use_cases.refresh_token import RefreshToken
from app.modules.auth.presentation.admin_dependencies import (
    get_admin_login_use_case,
    get_admin_logout_use_case,
    get_admin_refresh_use_case,
    get_current_admin,
)
from app.modules.auth.presentation.admin_schemas import AdminAuthResponse, AdminResponse
from app.modules.auth.presentation.schemas import (
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    TokenResponse,
)

router = APIRouter(prefix="/admin/auth", tags=["Admin Authentication"])


@router.post("/login", response_model=AdminAuthResponse)
async def login(
    payload: LoginRequest,
    use_case: Annotated[LoginAdmin, Depends(get_admin_login_use_case)],
) -> AdminAuthResponse:
    result = await use_case.execute(
        LoginUserCommand(email=str(payload.email), password=payload.password)
    )
    return AdminAuthResponse.from_result(result)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshRequest,
    use_case: Annotated[RefreshToken, Depends(get_admin_refresh_use_case)],
) -> TokenResponse:
    tokens = await use_case.execute(
        RefreshTokenCommand(refresh_token=payload.refresh_token)
    )
    return TokenResponse.from_tokens(tokens)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    payload: RefreshRequest,
    use_case: Annotated[LogoutUser, Depends(get_admin_logout_use_case)],
) -> MessageResponse:
    await use_case.execute(LogoutUserCommand(refresh_token=payload.refresh_token))
    return MessageResponse(message="Logged out successfully.")


@router.get("/me", response_model=AdminResponse)
async def me(
    admin: Annotated[AdminDTO, Depends(get_current_admin)],
) -> AdminResponse:
    return AdminResponse.from_dto(admin)

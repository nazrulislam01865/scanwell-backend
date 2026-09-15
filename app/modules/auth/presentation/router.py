from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.modules.auth.application.commands import (
    LoginUserCommand,
    RefreshTokenCommand,
    RegisterUserCommand,
    RequestLoginOtpCommand,
    ResendVerificationCommand,
    VerifyEmailCommand,
    VerifyLoginOtpCommand,
)
from app.modules.auth.application.queries import CurrentUserQuery
from app.modules.auth.application.use_cases.get_current_user import GetCurrentUser
from app.modules.auth.application.use_cases.login_user import LoginUser
from app.modules.auth.application.use_cases.refresh_token import RefreshToken
from app.modules.auth.application.use_cases.register_user import RegisterUser
from app.modules.auth.application.use_cases.request_login_otp import RequestLoginOtp
from app.modules.auth.application.use_cases.resend_verification import ResendVerification
from app.modules.auth.application.use_cases.verify_email import VerifyEmail
from app.modules.auth.application.use_cases.verify_login_otp import VerifyLoginOtp
from app.modules.auth.presentation.dependencies import (
    get_current_user_id,
    get_get_current_user_use_case,
    get_login_user_use_case,
    get_refresh_token_use_case,
    get_register_user_use_case,
    get_request_login_otp_use_case,
    get_resend_verification_use_case,
    get_verify_email_use_case,
    get_verify_login_otp_use_case,
)
from app.modules.auth.presentation.schemas import (
    AuthResponse,
    CodeDispatchResponse,
    EmailRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UserResponse,
    VerifyCodeRequest,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    use_case: Annotated[RegisterUser, Depends(get_register_user_use_case)],
) -> RegisterResponse:
    result = await use_case.execute(
        RegisterUserCommand(
            name=payload.name,
            email=str(payload.email),
            phone=payload.phone,
            password=payload.password,
            preferred_login_method=payload.preferred_login_method,
        )
    )
    return RegisterResponse.from_result(result)


@router.post("/verify-email", response_model=AuthResponse)
async def verify_email(
    payload: VerifyCodeRequest,
    use_case: Annotated[VerifyEmail, Depends(get_verify_email_use_case)],
) -> AuthResponse:
    result = await use_case.execute(
        VerifyEmailCommand(email=str(payload.email), code=payload.code)
    )
    return AuthResponse.from_result(result)


@router.post(
    "/resend-verification",
    response_model=CodeDispatchResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def resend_verification(
    payload: EmailRequest,
    use_case: Annotated[ResendVerification, Depends(get_resend_verification_use_case)],
) -> CodeDispatchResponse:
    result = await use_case.execute(ResendVerificationCommand(email=str(payload.email)))
    return CodeDispatchResponse.from_result(result)


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    use_case: Annotated[LoginUser, Depends(get_login_user_use_case)],
) -> AuthResponse:
    result = await use_case.execute(
        LoginUserCommand(email=str(payload.email), password=payload.password)
    )
    return AuthResponse.from_result(result)


@router.post(
    "/login/otp/request",
    response_model=CodeDispatchResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def request_login_otp(
    payload: EmailRequest,
    use_case: Annotated[RequestLoginOtp, Depends(get_request_login_otp_use_case)],
) -> CodeDispatchResponse:
    result = await use_case.execute(RequestLoginOtpCommand(email=str(payload.email)))
    return CodeDispatchResponse.from_result(result)


@router.post("/login/otp/verify", response_model=AuthResponse)
async def verify_login_otp(
    payload: VerifyCodeRequest,
    use_case: Annotated[VerifyLoginOtp, Depends(get_verify_login_otp_use_case)],
) -> AuthResponse:
    result = await use_case.execute(
        VerifyLoginOtpCommand(email=str(payload.email), code=payload.code)
    )
    return AuthResponse.from_result(result)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshRequest,
    use_case: Annotated[RefreshToken, Depends(get_refresh_token_use_case)],
) -> TokenResponse:
    tokens = await use_case.execute(RefreshTokenCommand(refresh_token=payload.refresh_token))
    return TokenResponse.from_tokens(tokens)


@router.get("/me", response_model=UserResponse)
async def me(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    use_case: Annotated[GetCurrentUser, Depends(get_get_current_user_use_case)],
) -> UserResponse:
    user = await use_case.execute(CurrentUserQuery(user_id=user_id))
    return UserResponse.from_dto(user)

from app.core.exceptions.base import AppException


class AuthError(AppException):
    code = "AUTH_ERROR"
    message = "Authentication request failed."
    status_code = 400


class EmailAlreadyRegisteredError(AuthError):
    code = "EMAIL_ALREADY_REGISTERED"
    message = "An account with this email address already exists."
    status_code = 409


class InvalidCredentialsError(AuthError):
    code = "INVALID_CREDENTIALS"
    message = "Email or password is incorrect."
    status_code = 401


class EmailNotVerifiedError(AuthError):
    code = "EMAIL_NOT_VERIFIED"
    message = "Verify your email address before logging in."
    status_code = 403


class AccountDisabledError(AuthError):
    code = "ACCOUNT_DISABLED"
    message = "This account is disabled."
    status_code = 403


class InvalidVerificationCodeError(AuthError):
    code = "INVALID_VERIFICATION_CODE"
    message = "The verification code is invalid."
    status_code = 401


class VerificationCodeExpiredError(AuthError):
    code = "VERIFICATION_CODE_EXPIRED"
    message = "The verification code has expired. Request a new code."
    status_code = 401


class VerificationAttemptsExceededError(AuthError):
    code = "VERIFICATION_ATTEMPTS_EXCEEDED"
    message = "Too many invalid verification attempts. Request a new code."
    status_code = 401


class InvalidAuthTokenError(AuthError):
    code = "INVALID_AUTH_TOKEN"
    message = "The authentication token is invalid or expired."
    status_code = 401


class AuthUserNotFoundError(AuthError):
    code = "AUTH_USER_NOT_FOUND"
    message = "The authenticated user could not be found."
    status_code = 401


class EmailDeliveryFailedError(AuthError):
    code = "EMAIL_DELIVERY_FAILED"

    message = (
        "We could not send the verification "
        "email. Please try again shortly."
    )

    status_code = 503
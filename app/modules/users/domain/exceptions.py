from app.core.exceptions.base import AppException


class UserError(AppException):
    code = "USER_ERROR"
    message = "The user request could not be completed."
    status_code = 400


class UserNotFoundError(UserError):
    code = "USER_NOT_FOUND"
    message = "The user account could not be found."
    status_code = 404


class UserAccountInactiveError(UserError):
    code = "USER_ACCOUNT_INACTIVE"
    message = "This user account is inactive."
    status_code = 403


class InvalidAccountPasswordError(UserError):
    code = "INVALID_ACCOUNT_PASSWORD"
    message = "The current password is incorrect."
    status_code = 401

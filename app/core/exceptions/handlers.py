from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions.base import AppException


async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": {
                "code": exc.code,
                "message": exc.message,
            }
        },
    )


from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


class BusinessError(Exception):
    status_code = 400
    code = "BUSINESS_ERROR"
    message = "Business error"

    def __init__(self, message: str | None = None):
        self.message = message or type(self).message
        super().__init__(self.message)


class NotFound(BusinessError):
    status_code = 404
    code = "NOT_FOUND"
    message = "Resource not found"


class Forbidden(BusinessError):
    status_code = 403
    code = "FORBIDDEN"
    message = "Access denied"


class Conflict(BusinessError):
    status_code = 409
    code = "CONFLICT"
    message = "Resource conflict"


class RateLimited(BusinessError):
    status_code = 429
    code = "RATE_LIMITED"
    message = "Too many requests"


async def business_error_handler(
    request: Request, exc: BusinessError
):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        },
    )


async def http_error_handler(
    request: Request, exc: StarletteHTTPException
):
    code_by_status = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        429: "RATE_LIMITED",
        500: "INTERNAL_SERVER_ERROR",
    }

    message = exc.detail
    if not isinstance(message, str):
        message = "HTTP error"

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": code_by_status.get(
                    exc.status_code, "HTTP_ERROR"
                ),
                "message": message,
            }
        },
        headers=getattr(exc, "headers", None),
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError
):
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request data",
            }
        },
    )


async def unexpected_error_handler(
    request: Request, exc: Exception
):
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
            }
        },
    )

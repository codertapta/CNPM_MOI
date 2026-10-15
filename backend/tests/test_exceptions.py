import json

import pytest
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import (
    BusinessError,
    Conflict,
    Forbidden,
    NotFound,
    RateLimited,
    business_error_handler,
    http_error_handler,
    unexpected_error_handler,
    validation_error_handler,
)


@pytest.fixture
def mock_request():
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/test",
            "raw_path": b"/test",
            "query_string": b"",
            "headers": [],
            "server": ("testserver", 80),
            "client": ("testclient", 12345),
        }
    )


@pytest.mark.parametrize(
    ("error_class", "status_code", "code", "default_message"),
    [
        (BusinessError, 400, "BUSINESS_ERROR", "Business error"),
        (NotFound, 404, "NOT_FOUND", "Resource not found"),
        (Forbidden, 403, "FORBIDDEN", "Access denied"),
        (Conflict, 409, "CONFLICT", "Resource conflict"),
        (RateLimited, 429, "RATE_LIMITED", "Too many requests"),
    ],
)
def test_business_error_defaults(error_class, status_code, code, default_message):
    error = error_class()

    assert error.status_code == status_code
    assert error.code == code
    assert error.message == default_message


def test_business_error_custom_message():
    error = NotFound("POI not found")

    assert error.message == "POI not found"
    assert str(error) == "POI not found"


@pytest.mark.anyio
async def test_business_error_handler(mock_request):
    response = await business_error_handler(mock_request, NotFound("Missing POI"))

    assert response.status_code == 404
    assert json.loads(response.body) == {
        "error": {
            "code": "NOT_FOUND",
            "message": "Missing POI",
        }
    }


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("status_code", "detail", "expected_code", "expected_message"),
    [
        (400, "Bad input", "BAD_REQUEST", "Bad input"),
        (401, "Login required", "UNAUTHORIZED", "Login required"),
        (403, "Forbidden", "FORBIDDEN", "Forbidden"),
        (404, "Missing", "NOT_FOUND", "Missing"),
        (405, "Wrong method", "METHOD_NOT_ALLOWED", "Wrong method"),
        (409, "Conflict", "CONFLICT", "Conflict"),
        (429, "Slow down", "RATE_LIMITED", "Slow down"),
        (500, "Failure", "INTERNAL_SERVER_ERROR", "Failure"),
        (418, "Teapot", "HTTP_ERROR", "Teapot"),
        (400, {"detail": "invalid"}, "BAD_REQUEST", "HTTP error"),
    ],
)
async def test_http_error_handler(
    mock_request, status_code, detail, expected_code, expected_message
):
    error = StarletteHTTPException(
        status_code=status_code,
        detail=detail,
        headers={"X-Test": "present"},
    )

    response = await http_error_handler(mock_request, error)

    assert response.status_code == status_code
    assert response.headers["X-Test"] == "present"
    assert json.loads(response.body) == {
        "error": {
            "code": expected_code,
            "message": expected_message,
        }
    }


@pytest.mark.anyio
async def test_validation_error_handler(mock_request):
    error = RequestValidationError(
        [
            {
                "type": "missing",
                "loc": ("query", "lat"),
                "msg": "Field required",
                "input": None,
            }
        ]
    )

    response = await validation_error_handler(mock_request, error)

    assert response.status_code == 400
    assert json.loads(response.body) == {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Invalid request data",
        }
    }


@pytest.mark.anyio
async def test_unexpected_error_handler(mock_request):
    response = await unexpected_error_handler(
        mock_request, RuntimeError("private internal details")
    )

    assert response.status_code == 500
    assert json.loads(response.body) == {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
        }
    }
    assert b"private internal details" not in response.body

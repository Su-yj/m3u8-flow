from collections.abc import Callable
from typing import Any

from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.requests import Request
from fastapi.responses import JSONResponse


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "code": 422,
            "message": "参数校验失败",
            "data": {"errors": exc.errors()},
        },
    )


async def universal_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.status_code,
                "message": exc.detail if isinstance(exc.detail, str) else str(exc.detail),
                "data": None,
            },
        )
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "系统异常",
            "data": {"errors": [str(exc)]},
        },
    )


def get_app_exception_handlers() -> dict[type[Exception], Callable[..., Any]]:
    return {
        RequestValidationError: validation_exception_handler,
        Exception: universal_exception_handler,
    }

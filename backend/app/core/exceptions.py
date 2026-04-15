from collections.abc import Callable, Mapping, Sequence
from typing import Any

from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.requests import Request
from fastapi.responses import JSONResponse


def _sanitize_validation_errors(
    errors: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """
    FastAPI/Pydantic 的 errors() 可能在 ctx 中携带异常对象（如 ValueError），
    直接 JSON 序列化会失败，这里统一转为字符串。
    """
    sanitized: list[dict[str, Any]] = []
    for err in errors:
        e = dict(err)
        ctx = e.get("ctx")
        if isinstance(ctx, dict):
            new_ctx: dict[str, Any] = {}
            for k, v in ctx.items():
                new_ctx[k] = str(v) if isinstance(v, BaseException) else v
            e["ctx"] = new_ctx
        # 兜底：若未来出现其它不可序列化对象，尽量转字符串
        for k, v in list(e.items()):
            if isinstance(v, BaseException):
                e[k] = str(v)
        sanitized.append(e)
    return sanitized


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "code": 422,
            "message": "参数校验失败",
            "data": {"errors": _sanitize_validation_errors(exc.errors())},
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

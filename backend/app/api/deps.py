from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.utils.jwt import decode_jwt_token_or_401

from app.services.task_manager import TaskManager

_bearer_scheme = HTTPBearer(auto_error=False)


def get_task_manager(request: Request) -> TaskManager:

    return request.app.state.task_manager


async def jwt_auth_dependency(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> dict:
    """
    当 settings.auth=True 时强制校验 access token；
    否则直接放行（返回空 dict）。
    """
    if not settings.auth:
        return {}

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    decoded = decode_jwt_token_or_401(
        token,
        expired_detail="Access token expired",
        invalid_detail="Invalid access token",
    )

    if decoded.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not decoded.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return decoded

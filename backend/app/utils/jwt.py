import datetime
from typing import Literal

import jwt
from fastapi import HTTPException, status

from app.core.config import settings


def create_jwt_token(
    data: dict,
    token_type: Literal["access", "refresh"],
    expires_delta: datetime.timedelta,
) -> str:
    to_encode = data.copy()
    expire = datetime.datetime.now(settings.tz_info) + expires_delta
    to_encode.update({"exp": expire, "type": token_type})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def decode_jwt_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm],
    )


def decode_jwt_token_or_401(
    token: str,
    *,
    expired_detail: str,
    invalid_detail: str,
) -> dict:
    try:
        return decode_jwt_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=expired_detail,
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=invalid_detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings
from app.schemas.auth import RefreshTokenRequest, Token
from app.schemas.response import ResponseSchema
from app.utils.jwt import create_jwt_token, decode_jwt_token_or_401

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=ResponseSchema[Token])
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    if (
        settings.username != form_data.username
        or settings.password != form_data.password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = datetime.timedelta(
        minutes=settings.access_token_expire_minutes
    )
    refresh_token_expires = datetime.timedelta(
        minutes=settings.refresh_token_expire_minutes
    )
    access_token = create_jwt_token(
        data={"sub": form_data.username},
        token_type="access",
        expires_delta=access_token_expires,
    )
    refresh_token = create_jwt_token(
        data={"sub": form_data.username},
        token_type="refresh",
        expires_delta=refresh_token_expires,
    )
    return ResponseSchema(
        data=Token(
            access_token=access_token,
            refresh_token=refresh_token,
        ),
    )


@router.post("/refresh", response_model=ResponseSchema[Token])
async def refresh(payload: RefreshTokenRequest):
    decoded = decode_jwt_token_or_401(
        payload.refresh_token,
        expired_detail="Refresh token expired",
        invalid_detail="Invalid refresh token",
    )

    if decoded.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    subject = decoded.get("sub")
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    now = datetime.datetime.now(settings.tz_info)
    exp = decoded.get("exp")
    if exp is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token exp",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if isinstance(exp, datetime.datetime):
        exp_dt = exp
        if exp_dt.tzinfo is None:
            exp_dt = exp_dt.replace(tzinfo=settings.tz_info)
    else:
        try:
            exp_dt = datetime.datetime.fromtimestamp(float(exp), tz=settings.tz_info)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token exp",
                headers={"WWW-Authenticate": "Bearer"},
            )

    remaining_minutes = (exp_dt - now).total_seconds() / 60

    access_token_expires = datetime.timedelta(
        minutes=settings.access_token_expire_minutes
    )
    new_access_token = create_jwt_token(
        data={"sub": subject},
        token_type="access",
        expires_delta=access_token_expires,
    )

    new_refresh_token = payload.refresh_token
    if remaining_minutes <= settings.refresh_token_replace_minutes:
        refresh_token_expires = datetime.timedelta(
            minutes=settings.refresh_token_expire_minutes
        )
        new_refresh_token = create_jwt_token(
            data={"sub": subject},
            token_type="refresh",
            expires_delta=refresh_token_expires,
        )

    return ResponseSchema(
        data=Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
        ),
    )

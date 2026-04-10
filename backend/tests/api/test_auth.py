import datetime

import httpx
import pytest
from app.core.config import settings
from app.utils.jwt import create_jwt_token, decode_jwt_token


@pytest.fixture()
def _restore_auth_settings():
    original = {
        "username": settings.username,
        "password": settings.password,
        "refresh_token_replace_minutes": settings.refresh_token_replace_minutes,
    }
    yield
    settings.username = original["username"]
    settings.password = original["password"]
    settings.refresh_token_replace_minutes = original["refresh_token_replace_minutes"]


async def test_login_success(client: httpx.AsyncClient, _restore_auth_settings):
    settings.username = "admin"
    settings.password = "123456"

    resp = await client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "123456"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"] is not None
    assert isinstance(body["data"]["access_token"], str)
    assert isinstance(body["data"]["refresh_token"], str)
    assert body["data"]["token_type"] == "bearer"

    access_decoded = decode_jwt_token(body["data"]["access_token"])
    refresh_decoded = decode_jwt_token(body["data"]["refresh_token"])
    assert access_decoded["sub"] == "admin"
    assert access_decoded["type"] == "access"
    assert refresh_decoded["sub"] == "admin"
    assert refresh_decoded["type"] == "refresh"


async def test_login_wrong_credentials_401(
    client: httpx.AsyncClient, _restore_auth_settings
):
    settings.username = "admin"
    settings.password = "123456"

    resp = await client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "wrong"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Incorrect username or password"


async def test_refresh_success_no_replace_by_default(client: httpx.AsyncClient):
    original_replace = settings.refresh_token_replace_minutes
    settings.refresh_token_replace_minutes = 0
    refresh_token = create_jwt_token(
        data={"sub": "admin"},
        token_type="refresh",
        expires_delta=datetime.timedelta(minutes=60),
    )

    resp = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"] is not None
    assert body["data"]["refresh_token"] == refresh_token
    settings.refresh_token_replace_minutes = original_replace

    access_decoded = decode_jwt_token(body["data"]["access_token"])
    assert access_decoded["sub"] == "admin"
    assert access_decoded["type"] == "access"


async def test_refresh_replaces_refresh_token_when_near_expiry(
    client: httpx.AsyncClient, _restore_auth_settings
):
    settings.refresh_token_replace_minutes = 5

    refresh_token = create_jwt_token(
        data={"sub": "admin"},
        token_type="refresh",
        expires_delta=datetime.timedelta(minutes=1),
    )

    resp = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"] is not None
    assert body["data"]["refresh_token"] != refresh_token

    new_refresh_decoded = decode_jwt_token(body["data"]["refresh_token"])
    assert new_refresh_decoded["sub"] == "admin"
    assert new_refresh_decoded["type"] == "refresh"


async def test_refresh_with_access_token_401(client: httpx.AsyncClient):
    access_token = create_jwt_token(
        data={"sub": "admin"},
        token_type="access",
        expires_delta=datetime.timedelta(minutes=30),
    )
    resp = await client.post("/api/auth/refresh", json={"refresh_token": access_token})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid refresh token type"


async def test_refresh_expired_401(client: httpx.AsyncClient):
    expired_refresh = create_jwt_token(
        data={"sub": "admin"},
        token_type="refresh",
        expires_delta=datetime.timedelta(minutes=-1),
    )
    resp = await client.post(
        "/api/auth/refresh", json={"refresh_token": expired_refresh}
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Refresh token expired"

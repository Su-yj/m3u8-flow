import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from tortoise.context import tortoise_test_context
from tortoise.contrib.test import truncate_all_models

os.environ["TESTING"] = "1"


ClientManagerType = AsyncGenerator[httpx.AsyncClient, None]


@pytest.fixture(scope="session", autouse=True)
def _disable_auth_for_tests():
    from app.core.config import settings

    original = settings.auth
    settings.auth = False
    yield
    settings.auth = original


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
async def test_db():
    from app.core.config import settings

    async with tortoise_test_context(
        ["app.models"],
        timezone=settings.tz,
    ) as ctx:
        yield ctx


@asynccontextmanager
async def client_manager(
    app: FastAPI, base_url="http://test", **kw
) -> ClientManagerType:
    async with LifespanManager(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url=base_url, **kw) as c:
            yield c


@pytest.fixture(scope="function")
async def client() -> ClientManagerType:
    from app.main import app

    async with client_manager(app) as c:
        await truncate_all_models()
        yield c

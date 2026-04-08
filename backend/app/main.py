import contextlib
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from tortoise.contrib.fastapi import RegisterTortoise, tortoise_exception_handlers
from tortoise.migrations.api import migrate as run_migrations

from app.api.main import api_router
from app.core.config import settings
from app.core.db import ensure_sqlite_parent_dir
from app.core.exceptions import get_app_exception_handlers
from app.static_serving import mount_frontend_build


@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.getenv("TESTING") == "1":
        yield
    else:
        ensure_sqlite_parent_dir()
        await run_migrations(config=settings.tortoise_orm)
        async with RegisterTortoise(
            app,
            config=settings.tortoise_orm,
            generate_schemas=False,
            add_exception_handlers=False,
        ):
            from app.services.task_manager import task_manager

            await task_manager.initialize()
            app.state.task_manager = task_manager
            try:
                yield
            finally:
                with contextlib.suppress(Exception):
                    await task_manager.flush_running_tasks()


app = FastAPI(
    title="M3U8 Downloader",
    lifespan=lifespan,
    exception_handlers={
        **tortoise_exception_handlers(),
        **get_app_exception_handlers(),
    },
)
app.include_router(api_router)

# 非 /api 路径映射到构建目录（静态资源 + SPA history 回退）
mount_frontend_build(app, settings.project_root / "static")

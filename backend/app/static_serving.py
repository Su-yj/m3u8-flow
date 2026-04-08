"""
前端构建产物挂载。

与 API 路由解耦：`app.main` 只负责组装应用；具体「静态目录 + SPA 回退」策略集中在此模块，
便于单独测试或与将来 Nginx 反代方案对照。
"""

from __future__ import annotations

import asyncio
import stat
from pathlib import Path
from typing import Union

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException
from starlette.types import Scope

PathLike = Union[str, Path]


class SPAStaticFiles(StaticFiles):
    """
    Starlette 的 StaticFiles(html=True) 只会在「目录 URL」下找 index.html，
    或在没有命中文件时尝试 404.html；不会对 /completed 这类前端路由回退到根 index.html。
    在 404 时回退到 static/index.html，供 Vue Router history 模式刷新/直达使用。
    """

    async def get_response(self, path: str, scope: Scope):
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            if exc.status_code != 404 or not self.html:
                raise
            if scope["method"] not in ("GET", "HEAD"):
                raise
            full_path, stat_result = await asyncio.to_thread(self.lookup_path, "index.html")
            if stat_result and stat.S_ISREG(stat_result.st_mode):
                return self.file_response(full_path, stat_result, scope)
            raise


def mount_frontend_build(
    app: FastAPI,
    static_dir: PathLike,
    *,
    mount_path: str = "/",
    name: str = "static",
) -> None:
    """将非 API 流量映射到构建目录；必须在 `include_router(api_router)` 之后调用。"""
    app.mount(
        mount_path,
        SPAStaticFiles(directory=str(static_dir), html=True),
        name=name,
    )

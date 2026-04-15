from pathlib import Path

import httpx
import pytest

from app.api.deps import get_task_manager
from app.core.config import settings
from app.main import app
from app.models import Task


class _MockTaskManager:
    async def append_task(self, task: Task):
        return None


@pytest.fixture(autouse=True)
def override_task_manager_dependency():
    app.dependency_overrides[get_task_manager] = lambda: _MockTaskManager()
    yield
    app.dependency_overrides.pop(get_task_manager, None)


@pytest.mark.parametrize(
    "bad_name",
    [
        "../evil",
        "..\\evil",
        "..",
        "a/b",
        "a\\b",
    ],
)
async def test_create_task_rejects_path_traversal_name(
    client: httpx.AsyncClient, bad_name: str
):
    payload = {
        "name": bad_name,
        "m3u8_url": "https://example.com/new.m3u8",
        "download_dir": "downloads",
        "concurrency": 1,
        "speed_limit": None,
        "chunk_size": None,
        "proxy": None,
        "headers": None,
        "merge_video": True,
        "delete_cache": True,
    }
    resp = await client.post("/api/tasks/", json=payload)
    assert resp.status_code == 422


async def test_create_task_rejects_download_dir_outside_project(
    client: httpx.AsyncClient,
):
    project_root = settings.project_root.resolve()
    outside = (project_root.parent / "outside-downloads").resolve()
    if outside == settings.download_path.resolve():
        outside = (project_root.parent / "outside-downloads-2").resolve()

    payload = {
        "name": "ok",
        "m3u8_url": "https://example.com/new.m3u8",
        "download_dir": str(outside),
        "concurrency": 1,
        "speed_limit": None,
        "chunk_size": None,
        "proxy": None,
        "headers": None,
        "merge_video": True,
        "delete_cache": True,
    }
    resp = await client.post("/api/tasks/", json=payload)
    assert resp.status_code == 422


async def test_create_task_allows_global_download_dir_absolute(client: httpx.AsyncClient):
    payload = {
        "name": "create-safe",
        "m3u8_url": "https://example.com/new2.m3u8",
        "download_dir": str(settings.download_path),
        "concurrency": 1,
        "speed_limit": None,
        "chunk_size": None,
        "proxy": None,
        "headers": None,
        "merge_video": True,
        "delete_cache": True,
    }
    resp = await client.post("/api/tasks/", json=payload)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "create-safe"
    # download_dir 会被规范化为绝对路径
    assert Path(data["download_dir"]).resolve() == settings.download_path.resolve()


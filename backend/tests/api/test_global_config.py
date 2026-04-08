import httpx
import pytest
from app.api.deps import get_task_manager
from app.main import app
from app.models import GlobalConfig


class _MockTaskManager:
    async def update_task_concurrency(self, task_concurrency: int):
        return None


@pytest.fixture(autouse=True)
def override_task_manager_dependency():
    app.dependency_overrides[get_task_manager] = lambda: _MockTaskManager()
    yield
    app.dependency_overrides.pop(get_task_manager, None)


async def test_get_global_config(client: httpx.AsyncClient):
    # pytest 按名称排序会先跑 test_create_*，同会话共享 DB 时需显式清空
    assert not await GlobalConfig.exists()

    response = await client.get("/api/global_config/")
    assert response.status_code == 200
    result = response.json()
    assert result["data"] is not None

    assert await GlobalConfig.all().exists()

    response = await client.get("/api/global_config/")
    assert response.status_code == 200
    assert response.json()["data"]["id"] == result["data"]["id"]


async def test_update_global_config(client: httpx.AsyncClient):
    response = await client.patch("/api/global_config/", json={"task_concurrency": 2})
    assert response.status_code == 200
    result = response.json()
    assert result["data"] is not None
    assert result["data"]["task_concurrency"] == 2

    global_config = await GlobalConfig.first()
    assert global_config is not None
    assert global_config.task_concurrency == 2

    response = await client.patch("/api/global_config/", json={"task_concurrency": 1})
    assert response.status_code == 200
    assert response.json()["data"]["task_concurrency"] == 1

    await global_config.refresh_from_db()
    assert global_config.task_concurrency == 1


async def test_reset_global_config(client: httpx.AsyncClient):
    update_payload = {
        "download_dir": "custom-downloads",
        "concurrency": 8,
        "speed_limit": 4096,
        "chunk_size": 8192,
        "proxy": "http://127.0.0.1:7890",
        "headers": {"Authorization": "Bearer token"},
        "merge_video": False,
        "delete_cache": False,
        "task_concurrency": 3,
        "ffmpeg_path": "/usr/local/bin/ffmpeg",
    }
    update_response = await client.patch("/api/global_config/", json=update_payload)
    assert update_response.status_code == 200

    response = await client.post("/api/global_config/reset")
    assert response.status_code == 200
    result = response.json()
    data = result["data"]
    assert data is not None

    assert data["download_dir"] == "downloads"
    assert data["concurrency"] == 1
    assert data["speed_limit"] is None
    assert data["chunk_size"] is None
    assert data["proxy"] is None
    assert data["headers"] is None
    assert data["merge_video"] is True
    assert data["delete_cache"] is True
    assert data["task_concurrency"] == 1
    assert data["ffmpeg_path"] is None

    global_config = await GlobalConfig.first()
    assert global_config is not None
    assert global_config.download_dir == "downloads"
    assert global_config.concurrency == 1
    assert global_config.speed_limit is None
    assert global_config.chunk_size is None
    assert global_config.proxy is None
    assert global_config.headers is None
    assert global_config.merge_video is True
    assert global_config.delete_cache is True
    assert global_config.task_concurrency == 1
    assert global_config.ffmpeg_path is None

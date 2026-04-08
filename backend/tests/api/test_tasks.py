import httpx
import pytest
from app.api.deps import get_task_manager
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


async def test_get_tasks(client: httpx.AsyncClient):
    task1 = Task(
        m3u8_url="https://example.com/test.m3u8",
        name="test",
        download_dir="test_download",
        concurrency=1,
        speed_limit=1024 * 1024,
        chunk_size=1024 * 1024,
        proxy=None,
        headers=None,
    )
    task1.hash_id = task1.computed_hash_id(task1.m3u8_url)
    await task1.save()

    task2 = Task(
        m3u8_url="https://example.com/test2.m3u8",
        name="test2",
        download_dir="test_download",
        concurrency=1,
        speed_limit=1024 * 1024,
        chunk_size=1024 * 1024,
        proxy=None,
        headers=None,
    )
    task2.hash_id = task2.computed_hash_id(task2.m3u8_url)
    await task2.save()

    response = await client.get("/api/tasks/")
    assert response.status_code == 200
    result = response.json()
    assert result["data"] is not None
    assert result["total"] == 2
    assert result["total_pages"] == 1
    print(result)

    response = await client.get("/api/tasks/", params={"name": "test"})
    assert response.status_code == 200
    result = response.json()
    assert result["data"] is not None
    assert len(result["data"]) == 1
    assert result["data"][0]["name"] == "test"

    response = await client.get("/api/tasks/", params={"name__icontains": "test"})
    assert response.status_code == 200
    result = response.json()
    assert result["data"] is not None
    assert len(result["data"]) == 2

    response = await client.get("/api/tasks/", params={"name": "test1"})
    assert response.status_code == 200
    result = response.json()
    assert result["data"] is not None
    assert len(result["data"]) == 0

    response = await client.get(f"/api/tasks/{task1.id}")
    assert response.status_code == 200
    result = response.json()
    assert result["data"] is not None
    assert result["data"]["id"] == str(task1.id)
    print(result)


async def test_create_task_without_hash_id(client: httpx.AsyncClient):
    payload = {
        "name": "create-by-api",
        "m3u8_url": "https://example.com/new.m3u8",
        "download_dir": "downloads",
        "concurrency": 2,
        "speed_limit": None,
        "chunk_size": None,
        "proxy": None,
        "headers": None,
        "merge_video": True,
        "delete_cache": True,
    }
    response = await client.post("/api/tasks/", json=payload)
    assert response.status_code == 200
    result = response.json()
    assert result["data"] is not None
    assert result["data"]["name"] == payload["name"]
    assert result["data"]["m3u8_url"] == payload["m3u8_url"]
    assert result["data"]["hash_id"] is not None
    assert len(result["data"]["hash_id"]) == 64

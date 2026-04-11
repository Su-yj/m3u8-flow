import pytest

from app.models import GlobalConfig, Task
from app.utils.path_safety import build_task_download_path, validate_task_name


async def test_get_or_create_default_global_config():
    config, _ = await GlobalConfig.get_or_create()
    assert config is not None, "GlobalConfig not created"
    print(config.download_path)
    print(config.download_path.resolve())


async def test_create_task():
    task = Task(
        name="test",
        m3u8_url="https://example.com/test.m3u8",
        download_dir="test_download",
        concurrency=1,
        speed_limit=1024 * 1024,
        chunk_size=1024 * 1024,
        proxy=None,
        headers=None,
    )
    task.hash_id = task.computed_hash_id(task.m3u8_url)
    await task.save()
    print(task)

    assert await Task.filter(hash_id=task.hash_id).exists(), "Task not created"


def test_validate_task_name_rejects_invalid_values():
    invalid_names = ["", "   ", ".", "..", "../escape", "dir/name", "/abs/path", r"..\escape"]
    for name in invalid_names:
        with pytest.raises(ValueError):
            validate_task_name(name)


def test_build_task_download_path_stays_under_base_dir():
    target = build_task_download_path("/tmp/downloads", "safe-task")
    assert target.as_posix().endswith("/tmp/downloads/safe-task")


def test_build_task_download_path_rejects_escape_name():
    with pytest.raises(ValueError):
        build_task_download_path("/tmp/downloads", "../escape")

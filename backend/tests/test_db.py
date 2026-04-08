from app.models import GlobalConfig, Task


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

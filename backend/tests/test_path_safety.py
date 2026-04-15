import pytest
from app.core.config import settings
from app.utils.path_safety import (
    normalize_and_validate_download_dir,
    safe_join_under_base,
    validate_safe_task_name,
)


@pytest.mark.parametrize(
    "name",
    [
        "../evil",
        "..\\evil",
        "..",
        ".",
        "a/b",
        "a\\b",
        "C:evil",
        "a\x00b",
        "a..b",
        "  ..  ",
    ],
)
def test_validate_safe_task_name_rejects_dangerous(name: str):
    with pytest.raises(ValueError):
        validate_safe_task_name(name)


def test_validate_safe_task_name_accepts_normal():
    assert validate_safe_task_name("hello-world_01") == "hello-world_01"
    assert validate_safe_task_name("  ok  ") == "ok"


def test_normalize_and_validate_download_dir_allows_global_download_dir():
    p = normalize_and_validate_download_dir(str(settings.download_path))
    assert p.resolve() == settings.download_path.resolve()


def test_normalize_and_validate_download_dir_allows_relative_under_project_root():
    p = normalize_and_validate_download_dir("downloads")
    assert p.is_absolute()
    assert p.is_relative_to(settings.project_root.resolve())


def test_normalize_and_validate_download_dir_rejects_outside_project_root():
    project_root = settings.project_root.resolve()
    outside = (project_root.parent / "outside-downloads").resolve()
    # outside 不是 project_root 子路径，且不等于全局 download_dir
    if outside == settings.download_path.resolve():
        outside = (project_root.parent / "outside-downloads-2").resolve()
    with pytest.raises(ValueError):
        normalize_and_validate_download_dir(str(outside))


def test_safe_join_under_base_requires_final_path_under_base():
    base = settings.download_path.resolve()
    combined = safe_join_under_base(base, "task1")
    assert combined.is_relative_to(base)
    assert combined == (base / "task1").resolve()

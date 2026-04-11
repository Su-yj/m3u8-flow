from pathlib import Path


def validate_task_name(task_name: str) -> str:
    normalized_name = task_name.strip()
    if not normalized_name:
        raise ValueError("Task name cannot be empty")

    if "/" in normalized_name or "\\" in normalized_name:
        raise ValueError("Task name cannot contain path separators")

    path_candidate = Path(normalized_name)
    if path_candidate.is_absolute():
        raise ValueError("Task name cannot be an absolute path")

    if len(path_candidate.parts) != 1:
        raise ValueError("Task name cannot contain path separators")

    if normalized_name in {".", ".."}:
        raise ValueError("Task name cannot be '.' or '..'")

    return normalized_name


def build_task_download_path(download_dir: str, task_name: str) -> Path:
    base_dir = Path(download_dir).resolve()
    safe_task_name = validate_task_name(task_name)
    target_dir = (base_dir / safe_task_name).resolve()

    try:
        target_dir.relative_to(base_dir)
    except ValueError as exc:
        raise ValueError("Task download path escapes the download directory") from exc

    return target_dir

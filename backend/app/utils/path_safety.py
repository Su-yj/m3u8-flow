from __future__ import annotations

from pathlib import Path

from app.core.config import settings


def validate_safe_task_name(name: str) -> str:
    """
    任务名用于拼接路径时，必须可安全作为「单个目录名」使用。
    """
    if name is None:
        raise ValueError("任务名称不能为空")
    n = name.strip()
    if not n:
        raise ValueError("任务名称不能为空")
    if n in {".", ".."}:
        raise ValueError("任务名称不合法")
    # 禁止路径分隔符与 Windows 驱动器/协议等特殊字符
    if any(sep in n for sep in ("/", "\\")):
        raise ValueError("任务名称包含非法路径字符")
    if ":" in n:
        raise ValueError("任务名称包含非法字符 ':'")
    if "\x00" in n:
        raise ValueError("任务名称包含非法字符")
    # 禁止出现显式的上级目录片段（即便没有分隔符也直接拒绝）
    if ".." in n:
        raise ValueError("任务名称包含非法片段 '..'")
    return n


def normalize_and_validate_download_dir(download_dir: str) -> Path:
    """
    允许：
    - 与全局配置 settings.download_dir 一致
    - 位于项目根目录 settings.project_root 下（可为相对路径）
    返回绝对规范化后的 Path。
    """
    if download_dir is None:
        raise ValueError("下载目录不能为空")
    raw = str(download_dir).strip()
    if not raw:
        raise ValueError("下载目录不能为空")

    project_root = settings.project_root.resolve()
    global_download_dir = settings.download_path.resolve()

    p = Path(raw)
    if not p.is_absolute():
        p = (project_root / p).resolve()
    else:
        p = p.resolve()

    if p == global_download_dir:
        return p
    if p.is_relative_to(project_root):
        return p
    raise ValueError("下载目录不允许：必须与全局配置一致，或位于项目目录下")


def safe_join_under_base(base_dir: Path, child_name: str) -> Path:
    """
    安全拼接 base_dir / child_name，并校验最终路径仍在 base_dir 下。
    """
    base = Path(base_dir).resolve()
    name = validate_safe_task_name(child_name)
    combined = (base / name).resolve()
    if not combined.is_relative_to(base):
        raise ValueError("最终下载路径不安全：疑似路径穿越")
    return combined


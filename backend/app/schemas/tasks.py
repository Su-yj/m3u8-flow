import hashlib
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator
from tortoise.contrib.pydantic import PydanticModel, pydantic_model_creator

from app.core.config import settings
from app.models import Task
from app.utils.path_safety import (
    normalize_and_validate_download_dir,
    safe_join_under_base,
    validate_safe_task_name,
)

if TYPE_CHECKING:

    class TaskPydantic(Task, PydanticModel):  # pyright: ignore[reportGeneralTypeIssues]
        pass

else:
    TaskPydantic = pydantic_model_creator(Task, name="Task")


class TaskCreatePydantic(BaseModel):
    name: str
    m3u8_url: str
    download_dir: str = Field(default_factory=lambda: str(settings.download_path))
    concurrency: int = 1
    speed_limit: int | None = None
    chunk_size: int | None = None
    proxy: str | None = None
    headers: dict[str, str] | None = None
    merge_video: bool = True
    delete_cache: bool = True

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return validate_safe_task_name(v)

    @field_validator("download_dir")
    @classmethod
    def validate_download_dir(cls, v: str) -> str:
        return str(normalize_and_validate_download_dir(v))

    @model_validator(mode="after")
    def validate_final_path(self) -> "TaskCreatePydantic":
        # 组合最终下载目录后再校验：download_dir / name 必须仍在 download_dir 下
        base = normalize_and_validate_download_dir(self.download_dir)
        safe_join_under_base(base, self.name)
        # 确保落盘/入库的是规范化后的绝对路径
        self.download_dir = str(base)
        return self

    @computed_field(title="任务哈希ID")
    @property
    def hash_id(self) -> str:
        return hashlib.sha256(self.m3u8_url.encode()).hexdigest()


class TaskDeletePydantic(BaseModel):
    delete_cache: bool = Field(default=True, title="是否删除缓存")
    delete_downloaded_files: bool = Field(default=True, title="是否删除下载的文件")


class TaskUpdatePydantic(BaseModel):
    concurrency: int | None = Field(default=None, title="协程并发数")
    speed_limit: int | None = Field(default=None, title="下载速度限制")
    chunk_size: int | None = Field(default=None, title="下载分块大小")
    proxy: str | None = Field(default=None, title="代理地址")
    headers: dict[str, str] | None = Field(default=None, title="请求头")

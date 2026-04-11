import hashlib
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, computed_field, field_validator
from tortoise.contrib.pydantic import PydanticModel, pydantic_model_creator

from app.models import Task
from app.utils.path_safety import validate_task_name

if TYPE_CHECKING:

    class TaskPydantic(Task, PydanticModel):  # pyright: ignore[reportGeneralTypeIssues]
        pass

else:
    TaskPydantic = pydantic_model_creator(Task, name="Task")


class TaskCreatePydantic(BaseModel):
    name: str
    m3u8_url: str
    download_dir: str = "downloads"
    concurrency: int = 1
    speed_limit: int | None = None
    chunk_size: int | None = None
    proxy: str | None = None
    headers: dict[str, str] | None = None
    merge_video: bool = True
    delete_cache: bool = True

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return validate_task_name(value)

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

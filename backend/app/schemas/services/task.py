from functools import cached_property
from pathlib import Path

import m3u8
from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.interfaces.task import TaskStatus
from app.schemas.services.downloader import DownloadConfig, DownloadInfo


class TaskConfig(BaseModel):
    m3u8_url: str = Field(title="M3U8 URL")
    task_name: str = Field(title="任务名称")
    download_dir: str = Field(title="下载目录")
    concurrency: int = Field(default=1, title="协程并发数")
    speed_limit: int | None = Field(default=None, title="下载速度限制")
    chunk_size: int | None = Field(default=None, title="下载分块大小")
    proxy: str | None = Field(default=None, title="代理地址")
    headers: dict[str, str] | None = Field(default=None, title="请求头")
    merge_video: bool = Field(default=True, title="是否合并视频")
    delete_cache: bool = Field(default=True, title="是否删除缓存")

    @computed_field(title="下载路径")
    @cached_property
    def download_path(self) -> Path:
        return Path(self.download_dir)

    @computed_field(title="缓存路径")
    @cached_property
    def cache_path(self) -> Path:
        return self.download_path / ".cache"

    def to_download_config(self, playlist: m3u8.M3U8) -> DownloadConfig:
        return DownloadConfig(
            playlist=playlist,
            download_dir=self.download_dir,
            concurrency=self.concurrency,
            speed_limit=self.speed_limit,
            chunk_size=self.chunk_size,
            proxy=self.proxy,
            headers=self.headers,
        )

    def to_task_info(
        self, status: TaskStatus, download_info: DownloadInfo | None
    ) -> "TaskInfo":
        return TaskInfo(
            m3u8_url=self.m3u8_url,
            task_name=self.task_name,
            download_dir=self.download_dir,
            concurrency=self.concurrency,
            speed_limit=self.speed_limit,
            chunk_size=self.chunk_size,
            proxy=self.proxy,
            headers=self.headers,
            merge_video=self.merge_video,
            delete_cache=self.delete_cache,
            status=status,
            download_info=download_info,
        )


class TaskInfo(TaskConfig):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    status: TaskStatus = Field(default=TaskStatus.PENDING, title="任务状态")
    download_info: DownloadInfo | None = Field(default=None, title="下载信息")

    @computed_field(title="总片段数")
    @property
    def total_segments(self) -> int:
        return self.download_info.total_segments if self.download_info else 0

    @computed_field(title="已下载片段数")
    @property
    def downloaded_segments(self) -> int:
        return self.download_info.downloaded_segments if self.download_info else 0

    @computed_field(title="失败片段数")
    @property
    def failed_segments(self) -> int:
        return self.download_info.failed_segments if self.download_info else 0

    @computed_field(title="总大小")
    @property
    def total_size(self) -> int:
        return self.download_info.total_size if self.download_info else 0

    @computed_field(title="速度")
    @property
    def speed(self) -> float:
        return self.download_info.speed if self.download_info else 0

    @computed_field(title="进度")
    @property
    def progress(self) -> float:
        return self.download_info.progress if self.download_info else 0

    @computed_field(title="预计剩余时间")
    @property
    def eta(self) -> float | None:
        return self.download_info.eta if self.download_info else None

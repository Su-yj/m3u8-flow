import enum
from abc import ABC, abstractmethod
from typing import Generic, Protocol, TypeVar, runtime_checkable

import m3u8

from app.interfaces.downloader import BaseDownloader
from app.interfaces.merge_parser import BaseMergeParser

DownloaderType = TypeVar("DownloaderType", bound=BaseDownloader)
MergeParserType = TypeVar("MergeParserType", bound=BaseMergeParser)


class TaskStatus(enum.StrEnum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    MERGING = "merging"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"

    @property
    def label(self) -> str:
        labels = {
            TaskStatus.PENDING: "等待中",
            TaskStatus.DOWNLOADING: "下载中",
            TaskStatus.MERGING: "合并中",
            TaskStatus.COMPLETED: "已完成",
            TaskStatus.FAILED: "失败",
            TaskStatus.STOPPED: "已停止",
        }
        return labels[self]


@runtime_checkable
class TaskConfig(Protocol):
    m3u8_url: str
    task_name: str
    download_dir: str
    concurrency: int
    speed_limit: int | None
    chunk_size: int | None
    proxy: str | None
    headers: dict[str, str] | None


@runtime_checkable
class TaskInfo(Protocol):
    @property
    def status(self) -> TaskStatus: ...

    @property
    def total_segments(self) -> int: ...

    @property
    def downloaded_segments(self) -> int: ...

    @property
    def failed_segments(self) -> int: ...

    @property
    def total_size(self) -> int: ...

    @property
    def speed(self) -> float: ...

    @property
    def progress(self) -> float: ...

    @property
    def eta(self) -> float | None: ...

    @property
    def m3u8_url(self) -> str: ...

    @property
    def task_name(self) -> str: ...

    @property
    def download_dir(self) -> str: ...

    @property
    def concurrency(self) -> int: ...

    @property
    def speed_limit(self) -> int | None: ...

    @property
    def chunk_size(self) -> int | None: ...

    @property
    def proxy(self) -> str | None: ...

    @property
    def headers(self) -> dict[str, str] | None: ...


TaskConfigType = TypeVar("TaskConfigType", bound=TaskConfig)
TaskInfoType = TypeVar("TaskInfoType", bound=TaskInfo)


class BaseTask(
    ABC, Generic[TaskConfigType, TaskInfoType, DownloaderType, MergeParserType]
):
    def __init__(self, config: TaskConfigType):
        self.config: TaskConfigType = config
        self.downloader: DownloaderType | None = None
        self.merge_parser: MergeParserType | None = None
        self.playlist: m3u8.M3U8 | None = None
        self.status: TaskStatus = TaskStatus.PENDING

    @abstractmethod
    def get_info(self) -> TaskInfoType:
        """获取任务信息"""
        raise NotImplementedError

    @abstractmethod
    async def start(self):
        """开始任务"""
        raise NotImplementedError

    @abstractmethod
    async def stop(self):
        """停止任务（一般面向用户的主动操作）"""
        raise NotImplementedError

    @abstractmethod
    async def cancel(self):
        """取消任务（不面向用户的操作，主要是内部任务并发数改变后，用于把任务状态从下载中改为等待）"""
        raise NotImplementedError

    @abstractmethod
    async def merge_segments(self, *args, **kwargs):
        """合并视频片段"""
        raise NotImplementedError

    @abstractmethod
    async def clean_cache(self):
        """清理缓存"""
        raise NotImplementedError

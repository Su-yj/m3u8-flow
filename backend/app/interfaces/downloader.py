from abc import ABC, abstractmethod
from typing import Generic, Protocol, TypeVar, runtime_checkable

import m3u8


@runtime_checkable
class DownloadConfig(Protocol):
    playlist: m3u8.M3U8
    download_dir: str
    concurrency: int
    speed_limit: int | None
    chunk_size: int | None
    proxy: str | None
    headers: dict[str, str] | None


@runtime_checkable
class DownloadInfo(Protocol):
    @property
    def total_segments(self) -> int: ...

    @property
    def downloaded_segments(self) -> int: ...

    @property
    def failed_segments(self) -> int: ...

    @property
    def total_size(self) -> int: ...

    @property
    def total_duration(self) -> float: ...

    @property
    def speed(self) -> float: ...

    @property
    def progress(self) -> float: ...

    @property
    def eta(self) -> float | None: ...


DownloadConfigType = TypeVar("DownloadConfigType", bound=DownloadConfig)
DownloadInfoType = TypeVar("DownloadInfoType", bound=DownloadInfo)


class BaseDownloader(ABC, Generic[DownloadConfigType, DownloadInfoType]):
    def __init__(self, config: DownloadConfigType):
        self.config: DownloadConfigType = config

    @abstractmethod
    def get_info(self) -> DownloadInfoType:
        """获取下载信息"""
        raise NotImplementedError

    @abstractmethod
    async def start(self):
        """开始下载"""
        raise NotImplementedError

    @abstractmethod
    async def stop(self):
        """停止下载"""
        raise NotImplementedError

    @abstractmethod
    def update_concurrency(self, concurrency: int):
        """更新并发数"""
        raise NotImplementedError

    @abstractmethod
    def update_speed_limit(self, speed_limit: int | None):
        """更新下载速度限制"""
        raise NotImplementedError

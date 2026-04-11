from functools import cached_property
from pathlib import Path

import m3u8
from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.services.speed_monitor import SpeedMonitor


class DownloadConfig(BaseModel):
    """下载配置"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    playlist: m3u8.M3U8 = Field(title="播放列表")
    download_dir: str = Field(title="下载目录")
    concurrency: int = Field(default=1, title="协程并发数")
    speed_limit: int | None = Field(
        default=None,
        title="下载速度限制",
        description="单位：字节/秒，默认 None，即不限速",
    )
    chunk_size: int | None = Field(
        default=None,
        title="下载分块大小",
        description="单位：字节，默认为 None",
    )
    proxy: str | None = Field(
        default=None,
        title="代理地址",
        description="如：http://127.0.0.1:7890，默认 None，即不使用代理",
    )
    headers: dict[str, str] | None = Field(default=None, title="请求头")
    segment_max_retries: int = Field(
        default=5,
        ge=1,
        title="分片下载最大尝试次数",
        description="含首次请求；流式读取阶段的超时、断连等会按此次数重试",
    )
    segment_retry_backoff: float = Field(
        default=0.5,
        ge=0.0,
        title="分片重试初始退避秒数",
        description="指数退避：第 n 次重试前等待 backoff * 2^n 秒",
    )

    @computed_field(title="下载路径")
    @cached_property
    def download_path(self) -> Path:
        return Path(self.download_dir)


class DownloadInfo(BaseModel):
    """下载信息"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    total_segments: int = Field(default=0, title="总片段数")
    downloaded_segments: int = Field(default=0, title="已下载片段数")
    failed_segments: int = Field(default=0, title="失败片段数")
    total_size: int = Field(default=0, title="已下载文件大小")
    total_duration: float = Field(default=0, title="总时长")

    speed_monitor: SpeedMonitor = Field(default_factory=SpeedMonitor, title="速度监控")

    @computed_field(title="平均速度", description="单位：字节/秒")
    @property
    def speed(self) -> float:
        return self.speed_monitor.current_speed

    @computed_field(title="进度", description="单位：%")
    @property
    def progress(self) -> float:
        return self.downloaded_segments / self.total_segments * 100

    @computed_field(title="预计剩余时间", description="单位：秒")
    @property
    def eta(self) -> float | None:
        try:
            return (
                (self.total_duration - self.downloaded_segments)
                * (self.total_size / self.downloaded_segments)
                / self.speed
            )
        except ZeroDivisionError:
            return None

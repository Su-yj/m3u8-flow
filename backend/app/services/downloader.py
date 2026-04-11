import asyncio
from pathlib import Path

import aiofiles
import httpx
import m3u8
from aiolimiter import AsyncLimiter

from app.core.log import logger
from app.interfaces.downloader import BaseDownloader
from app.schemas.services.downloader import DownloadConfig, DownloadInfo
from app.services.speed_monitor import SpeedMonitor
from app.utils.http_retries import get_transport


def _is_retryable_segment_error(exc: BaseException) -> bool:
    """流式下载阶段可重试的网络/超时类错误（transport 层通常不会在 body 读取时重试）。"""
    if isinstance(exc, httpx.TimeoutException):
        return True
    if isinstance(exc, httpx.NetworkError):
        return True
    if isinstance(exc, httpx.RemoteProtocolError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500
    return False


class Downloader(BaseDownloader[DownloadConfig, DownloadInfo]):
    def __init__(self, config: DownloadConfig):
        """下载器，用于下载 M3U8 播放列表中的片段"""
        super().__init__(config)
        # 速度监控
        self.speed_monitor = SpeedMonitor(1)
        # 下载状态
        self.info = DownloadInfo(
            speed_monitor=self.speed_monitor,
            total_segments=len(self.config.playlist.segments),
            total_duration=sum(
                (segment.duration or 0.0) for segment in self.config.playlist.segments
            ),
        )
        # 并发控制
        self._semaphore = asyncio.Semaphore(self.config.concurrency)
        # 令牌桶限流器
        self.rate_limiter = (
            AsyncLimiter(self.config.speed_limit, 1)
            if self.config.speed_limit
            else None
        )
        # 停止事件
        self.stop_event = asyncio.Event()

    def get_info(self) -> DownloadInfo:
        return self.info

    def update_concurrency(self, concurrency: int):
        """更新并发数"""
        self.config.concurrency = concurrency
        self._semaphore._value = self.config.concurrency

    def update_speed_limit(self, speed_limit: int | None):
        """更新下载速度限制"""
        self.config.speed_limit = speed_limit
        if self.config.speed_limit:
            if self.rate_limiter:
                self.rate_limiter.max_rate = self.config.speed_limit
            else:
                self.rate_limiter = AsyncLimiter(self.config.speed_limit, 1)
        else:
            self.rate_limiter = None

    def _check_stopped(self):
        """检查是否停止"""
        if self.stop_event.is_set():
            raise asyncio.CancelledError

    async def download_segment(
        self, client: httpx.AsyncClient, segment: m3u8.Segment, download_path: Path
    ):
        async with self._semaphore:
            max_attempts = self.config.segment_max_retries
            backoff = self.config.segment_retry_backoff

            for attempt in range(max_attempts):
                try:
                    self._check_stopped()
                    async with client.stream("GET", segment.absolute_uri) as response:
                        response.raise_for_status()
                        self._check_stopped()
                        async with aiofiles.open(download_path, "wb") as f:
                            async for chunk in response.aiter_bytes(
                                self.config.chunk_size
                            ):
                                self._check_stopped()

                                chunk_size = len(chunk)
                                if self.rate_limiter:
                                    await self.rate_limiter.acquire(chunk_size)
                                await f.write(chunk)
                                self.info.speed_monitor.add_sample(chunk_size)
                        self.info.total_size += download_path.stat().st_size
                        self.info.downloaded_segments += 1
                    return
                except asyncio.CancelledError:
                    if download_path.exists():
                        download_path.unlink()
                    raise
                except Exception as e:
                    if download_path.exists():
                        download_path.unlink()

                    if not _is_retryable_segment_error(e):
                        logger.exception(f"Download segment failed: {e}")
                        self.info.failed_segments += 1
                        return

                    if attempt >= max_attempts - 1:
                        logger.exception(
                            f"Download segment failed after {max_attempts} attempts: {e}"
                        )
                        self.info.failed_segments += 1
                        return

                    delay = backoff * (2**attempt)
                    logger.warning(
                        "Segment download attempt %s/%s failed (%s: %s), retrying in %.2fs",
                        attempt + 1,
                        max_attempts,
                        type(e).__name__,
                        e,
                        delay,
                    )
                    await asyncio.sleep(delay)

    async def start(self):
        # 创建下载目录
        self.config.download_path.mkdir(parents=True, exist_ok=True)
        transport = get_transport()
        async with httpx.AsyncClient(
            proxy=self.config.proxy,
            headers=self.config.headers,
            http2=True,
            transport=transport,
        ) as client:
            # 计算片段编号位数
            number_of_total = len(str(self.info.total_segments)) + 2
            format_string = f"{{:0{number_of_total}d}}"

            tasks = []
            for index, segment in enumerate(self.config.playlist.segments):
                download_path = (
                    self.config.download_path / f"{format_string.format(index)}.ts"
                )
                # 如果文件已存在，则跳过
                if download_path.exists():
                    self.info.downloaded_segments += 1
                    self.info.total_size += download_path.stat().st_size
                    continue
                tasks.append(
                    self.download_segment(
                        client=client,
                        segment=segment,
                        download_path=download_path,
                    )
                )
            await asyncio.gather(*tasks)

    async def stop(self):
        self.stop_event.set()

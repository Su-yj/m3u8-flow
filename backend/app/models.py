import asyncio
import contextlib
import hashlib
import shutil
import uuid
from functools import cached_property
from pathlib import Path

import httpx
import m3u8
from tortoise import Model, fields
from tortoise.validators import MinValueValidator

from app.core.log import logger
from app.interfaces.task import TaskStatus
from app.schemas.services.downloader import DownloadConfig
from app.services.downloader import Downloader
from app.services.merge_parser import MergeParser
from app.utils.http_retries import get_transport


class BaseConfig(Model):
    download_dir = fields.TextField(description="下载目录", default="downloads")
    concurrency = fields.IntField(description="协程并发数", default=1)
    speed_limit = fields.BigIntField(
        description="下载速度限制，单位：字节/秒，None 表示不限速",
        null=True,
        validators=[MinValueValidator(1)],
    )
    chunk_size = fields.BigIntField(
        description="下载分块大小，单位：字节",
        null=True,
        validators=[MinValueValidator(1)],
    )
    proxy = fields.TextField(description="代理地址", null=True)
    headers = fields.JSONField[dict[str, str] | None](description="请求头", null=True)
    merge_video = fields.BooleanField(
        description="是否合并视频，仅当任务完成后合并", default=True
    )
    delete_cache = fields.BooleanField(
        description="是否删除缓存，仅当任务完成后删除", default=True
    )

    @cached_property
    def download_path(self) -> Path:
        return Path(self.download_dir)

    class Meta:
        abstract = True


class Task(BaseConfig):
    id = fields.UUIDField(description="任务ID", primary_key=True, default=uuid.uuid4)
    hash_id = fields.CharField(description="任务哈希ID", max_length=64, db_index=True)
    name = fields.CharField(description="任务名称", max_length=255)
    m3u8_url = fields.TextField(description="M3U8 URL")
    status = fields.CharEnumField(
        description="任务状态", enum_type=TaskStatus, default=TaskStatus.PENDING
    )
    total_segments = fields.IntField(description="总片段数", default=0)
    downloaded_segments = fields.IntField(description="已下载片段数", default=0)
    failed_segments = fields.IntField(description="失败片段数", default=0)
    total_size = fields.BigIntField(description="已下载文件大小", default=0)
    total_duration = fields.FloatField(description="总时长", default=0)
    speed = fields.BigIntField(description="速度，单位：字节/秒", default=0)
    progress = fields.FloatField(description="进度，单位：%", default=0)
    eta = fields.FloatField(description="预计剩余时间，单位：秒", null=True)
    created_at = fields.DatetimeField(description="创建时间", auto_now_add=True)
    updated_at = fields.DatetimeField(description="更新时间", auto_now=True)

    playlist: m3u8.M3U8 | None = None
    downloader: Downloader | None = None
    merge_parser: MergeParser = MergeParser()
    checkpoint_interval_seconds: int = 10
    checkpoint_progress_delta: float = 1.0
    checkpoint_segments_delta: int = 20

    @cached_property
    def download_path(self) -> Path:
        return Path(self.download_dir) / self.name

    @cached_property
    def cache_path(self) -> Path:
        return self.download_path / ".cache"

    def __str__(self) -> str:
        return f"Task(id={self.id}, name={self.name})"

    def computed_hash_id(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()

    async def get_playlist(self) -> m3u8.M3U8:
        transport = get_transport()
        async with httpx.AsyncClient(
            proxy=self.proxy, headers=self.headers, transport=transport
        ) as client:
            response = await client.get(self.m3u8_url, follow_redirects=True)
            response.raise_for_status()
            return m3u8.loads(response.text, uri=self.m3u8_url)

    async def load(self):
        if not self.playlist:
            self.playlist = await self.get_playlist()
        if not self.downloader:
            self.downloader = Downloader(
                config=DownloadConfig(
                    playlist=self.playlist,
                    download_dir=str(self.cache_path),
                    concurrency=self.concurrency,
                    speed_limit=self.speed_limit,
                    chunk_size=self.chunk_size,
                    proxy=self.proxy,
                    headers=self.headers,
                )
            )

    async def sync_info(self):
        """同步任务信息"""
        if not self.downloader:
            return
        download_info = self.downloader.get_info()
        self.total_segments = download_info.total_segments
        self.downloaded_segments = download_info.downloaded_segments
        self.failed_segments = download_info.failed_segments
        self.total_size = download_info.total_size
        self.total_duration = download_info.total_duration
        # speed 字段在数据库/接口层是整数（字节/秒）；下载器侧可能是 float
        self.speed = int(download_info.speed)
        self.progress = download_info.progress
        self.eta = download_info.eta

    async def _save_runtime_checkpoint(self, force: bool = False):
        """按阈值保存运行时信息，降低崩溃时的数据丢失窗口。"""
        now = asyncio.get_running_loop().time()
        last_ts = getattr(self, "_last_checkpoint_ts", 0.0)
        last_progress = getattr(self, "_last_checkpoint_progress", 0.0)
        last_segments = getattr(self, "_last_checkpoint_segments", 0)

        interval_hit = now - last_ts >= self.checkpoint_interval_seconds
        progress_hit = (
            abs(self.progress - last_progress) >= self.checkpoint_progress_delta
        )
        segments_hit = (
            abs(self.downloaded_segments - last_segments)
            >= self.checkpoint_segments_delta
        )
        if not force and not (interval_hit or progress_hit or segments_hit):
            return

        await self.save(
            update_fields=[
                "status",
                "total_segments",
                "downloaded_segments",
                "failed_segments",
                "total_size",
                "total_duration",
                "speed",
                "progress",
                "eta",
            ]
        )
        self._last_checkpoint_ts = now
        self._last_checkpoint_progress = self.progress
        self._last_checkpoint_segments = self.downloaded_segments

    async def flush_checkpoint(self):
        """先从下载器同步运行时指标，再强制写入数据库。"""
        await self.sync_info()
        await self._save_runtime_checkpoint(force=True)

    async def is_download_completed(self) -> bool:
        """判断是否所有片段都已经下载到了缓存目录了"""
        if not self.playlist:
            self.playlist = await self.get_playlist()
        segments = list(self.cache_path.glob("*.ts"))
        return len(segments) == len(self.playlist.segments)

    async def merge_segments(self):
        """合并视频片段"""
        # 如果不需要合并视频，则直接返回
        if not self.merge_video:
            return
        # 如果缓存路径不存在，则直接返回
        if not self.cache_path.exists():
            raise ValueError("Cache path does not exist")
        # 如果所有片段还没有下载完成，则直接返回
        if not await self.is_download_completed():
            return
        segments = list(self.cache_path.glob("*.ts"))
        # 合并视频片段
        await self.merge_parser.merge(
            segments=segments,
            output_path=self.download_path / f"{self.name}.mp4",
            playlist=self.playlist,  # pyright: ignore[reportArgumentType]
        )

    async def clean_cache(self):
        """清理缓存"""
        # 如果不需要删除缓存或不需要合并视频，则直接返回
        if not self.delete_cache or not self.merge_video:
            return
        # 如果缓存路径不存在或不是目录，则直接返回
        if not self.cache_path.exists() or not self.cache_path.is_dir():
            return
        # 如果所有片段还没有下载完成，则直接返回
        if not await self.is_download_completed():
            return
        if self.cache_path.exists() and self.cache_path.is_dir():
            shutil.rmtree(self.cache_path)

    async def _periodic_sync_loop(self) -> None:
        """每 1 秒同步一次任务信息，由 start() 中的后台任务运行。"""
        while True:
            await asyncio.sleep(1)
            try:
                await self.sync_info()
                await self._save_runtime_checkpoint()
            except Exception:
                # 下载器未就绪或瞬时错误时不打断同步循环
                pass

    def reset_runtime_metrics(self):
        """重置运行时指标"""
        self.speed = 0
        self.eta = None

    async def start(self):
        """开始任务"""
        logger.info(">>> 开始任务")
        try:
            await self.load()
        except Exception:
            logger.exception("任务加载失败")
            self.status = TaskStatus.FAILED
            await self.flush_checkpoint()
            raise
        self._last_checkpoint_ts = 0.0
        self._last_checkpoint_progress = self.progress
        self._last_checkpoint_segments = self.downloaded_segments

        sync_task = asyncio.create_task(self._periodic_sync_loop())
        try:
            logger.info(">>> 设置任务状态为 DOWNLOADING")
            self.status = TaskStatus.DOWNLOADING
            await self.flush_checkpoint()
            await self.downloader.start()  # pyright: ignore[reportOptionalMemberAccess]
            if not await self.is_download_completed():
                raise ValueError("下载未完成")
            self.status = TaskStatus.MERGING
            await self.flush_checkpoint()
            await self.merge_segments()
            await self.clean_cache()
            self.status = TaskStatus.COMPLETED
            await self.flush_checkpoint()
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("任务执行失败")
            self.status = TaskStatus.FAILED
            await self.flush_checkpoint()
            raise
        finally:
            sync_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await sync_task
            # 当任务结束后，或因异常情况退出，把任务的某些信息置为默认值
            self.reset_runtime_metrics()
            # 最后保存到数据库
            await self.flush_checkpoint()

    async def stop(self):
        """停止任务（一般面向用户的主动操作）"""
        if self.downloader:
            await self.downloader.stop()
            self.status = TaskStatus.STOPPED
            await self.flush_checkpoint()

    async def cancel(self):
        """取消任务（不面向用户的操作，主要是内部任务并发数改变后，用于把任务状态从下载中改为等待）"""
        if self.downloader:
            await self.downloader.stop()
            self.status = TaskStatus.PENDING
            await self.flush_checkpoint()

    class Meta:
        table = "task"


class GlobalConfig(BaseConfig):
    id = fields.UUIDField(
        description="全局配置ID", primary_key=True, default=uuid.uuid4
    )
    task_concurrency = fields.IntField(description="任务并发数", default=1)
    ffmpeg_path = fields.TextField(description="FFmpeg 路径", null=True)

    class Meta:
        table = "global_config"

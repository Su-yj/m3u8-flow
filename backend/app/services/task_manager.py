import asyncio
import contextlib
import shutil
import uuid
from collections import OrderedDict

from app.interfaces.task import TaskStatus
from app.models import GlobalConfig, Task


class TaskManager:
    def __init__(self):
        self.pending_tasks: OrderedDict[uuid.UUID, Task] = OrderedDict[
            uuid.UUID, Task
        ]()
        # downloading_tasks 保存运行中的业务 Task 及其对应的 asyncio runner 句柄。
        self.downloading_tasks: OrderedDict[
            uuid.UUID, tuple[Task, asyncio.Task[None]]
        ] = OrderedDict[uuid.UUID, tuple[Task, asyncio.Task[None]]]()

        self.task_concurrency: int = 1
        # 停止/取消时等待 runner 收敛的超时时间，超时后会强制 cancel runner。
        self.runner_timeout_seconds: float = 5.0
        # 所有调度相关的内存状态修改都通过这把锁串行化，避免竞态。
        self._schedule_lock = asyncio.Lock()

    def get_task_by_id(self, task_id: uuid.UUID) -> Task | None:
        task = self.pending_tasks.get(task_id)
        if not task:
            task, _ = self.downloading_tasks.get(task_id, (None, None))
        return task

    def get_tasks(self) -> list[Task]:
        return [task for task, _ in self.downloading_tasks.values()] + list(
            self.pending_tasks.values()
        )

    async def flush_running_tasks(self):
        """将运行中任务的内存状态强制落库一次。"""
        async with self._schedule_lock:
            running_tasks = [task for task, _ in self.downloading_tasks.values()]
        for task in running_tasks:
            with contextlib.suppress(Exception):
                await task.flush_checkpoint()

    async def initialize(self):
        """初始化任务管理器"""
        async with self._schedule_lock:
            self.pending_tasks.clear()
            self.downloading_tasks.clear()

            # 获取全局配置
            global_config, _ = await GlobalConfig.get_or_create()
            self.task_concurrency = global_config.task_concurrency
            # 找寻正在下载和等待下载的任务
            tasks = await Task.filter(
                status__in=[TaskStatus.DOWNLOADING, TaskStatus.PENDING]
            ).order_by("created_at")
            # 对任务进行排序，正在下载的任务排在前面，等待下载的任务排在后面
            tasks.sort(
                key=lambda task: 0 if task.status == TaskStatus.DOWNLOADING else 1
            )
            for task in tasks:
                if task.status == TaskStatus.DOWNLOADING:
                    # 优先恢复 downloading，但启动数量不超过并发限制。
                    if len(self.downloading_tasks) < self.task_concurrency:
                        await self._start_task_locked(task, allow_downloading=True)
                    else:
                        # 超出并发限制的历史 downloading 任务回退为 pending。
                        task.status = TaskStatus.PENDING
                        await task.save()
                        self.pending_tasks[task.id] = task
                elif task.status == TaskStatus.PENDING:
                    self.pending_tasks[task.id] = task

            # 调度任务开始或停止
            await self._schedule_tasks_locked()

    async def schedule_tasks(self):
        """调度任务开始或停止"""
        async with self._schedule_lock:
            await self._schedule_tasks_locked()

    async def _schedule_tasks_locked(self):
        # 1. 检查当前的任务是否超过 task_concurrency，如果是那么将多余的任务停止并回退到 pending
        if len(self.downloading_tasks) > self.task_concurrency:
            while len(self.downloading_tasks) > self.task_concurrency:
                task_id = next(reversed(self.downloading_tasks))
                await self._converge_running_task_locked(
                    task_id=task_id,
                    action="cancel",
                    move_to_pending=True,
                )
            return

        # 2. 如果当前下载的任务小于 task_concurrency，那么将等待队列中的任务开始
        if len(self.downloading_tasks) < self.task_concurrency:
            while (
                len(self.downloading_tasks) < self.task_concurrency
                and len(self.pending_tasks) > 0
            ):
                _, task = self.pending_tasks.popitem(last=False)
                await self._start_task_locked(task)

    async def update_task_concurrency(self, task_concurrency: int):
        """更新任务并发数"""
        async with self._schedule_lock:
            if self.task_concurrency == task_concurrency:
                return
            self.task_concurrency = task_concurrency
            await self._schedule_tasks_locked()

    async def append_task(self, task: Task):
        """
        将任务添加到等待队列中
        """
        async with self._schedule_lock:
            if task.id in self.pending_tasks or task.id in self.downloading_tasks:
                return
            self.pending_tasks[task.id] = task
            await self._schedule_tasks_locked()

    async def start_task(self, task: Task):
        """开始任务"""
        async with self._schedule_lock:
            await self._start_task_locked(task)

    async def _start_task_locked(self, task: Task, allow_downloading: bool = False):
        await task.refresh_from_db()
        if task.id in self.downloading_tasks:
            return
        allowed_statuses = {
            TaskStatus.PENDING,
            TaskStatus.STOPPED,
            TaskStatus.FAILED,
            TaskStatus.MERGING,
        }
        if allow_downloading:
            allowed_statuses.add(TaskStatus.DOWNLOADING)
        if task.status not in allowed_statuses:
            return
        # 后台启动任务，不阻塞调度循环。
        runner_task = asyncio.create_task(task.start())
        self.downloading_tasks[task.id] = (task, runner_task)
        # runner 结束后异步回收内存状态并触发下一轮调度补位。
        runner_task.add_done_callback(
            lambda done_task, task_id=task.id: asyncio.create_task(
                self._on_task_done(task_id, done_task)
            )
        )

    async def _on_task_done(self, task_id: uuid.UUID, runner_task: asyncio.Task[None]):
        # 取一次 exception，避免 "Task exception was never retrieved" 警告
        with contextlib.suppress(asyncio.CancelledError, Exception):
            runner_task.exception()

        async with self._schedule_lock:
            managed_task = self.downloading_tasks.get(task_id)
            if managed_task and managed_task[1] is runner_task:
                self.downloading_tasks.pop(task_id, None)
            await self._schedule_tasks_locked()

    async def _converge_running_task_locked(
        self,
        task_id: uuid.UUID,
        action: str,
        move_to_pending: bool = False,
    ):
        managed_task = self.downloading_tasks.get(task_id)
        if not managed_task:
            return
        task, runner_task = managed_task

        if action == "stop":
            await task.stop()
        elif action == "cancel":
            await task.cancel()
        else:
            raise ValueError(f"Unsupported action: {action}")

        try:
            # 先软等待任务自行结束。
            await asyncio.wait_for(
                asyncio.shield(runner_task), timeout=self.runner_timeout_seconds
            )
        except asyncio.TimeoutError:
            # 超时后强制结束 runner，避免悬挂任务。
            runner_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await runner_task
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

        self.downloading_tasks.pop(task_id, None)
        with contextlib.suppress(asyncio.CancelledError, Exception):
            runner_task.exception()

        if move_to_pending:
            await task.refresh_from_db()
            if task.status != TaskStatus.PENDING:
                task.status = TaskStatus.PENDING
                await task.save()
            # 回退到等待队列，等待后续调度再启动。
            self.pending_tasks[task.id] = task

    async def stop_task(self, task: Task):
        """停止任务"""
        async with self._schedule_lock:
            if task.id in self.downloading_tasks:
                await self._converge_running_task_locked(
                    task_id=task.id,
                    action="stop",
                    move_to_pending=False,
                )
            self.pending_tasks.pop(task.id, None)
            await self._schedule_tasks_locked()

    async def remove_task(
        self, task: Task, delete_cache: bool, delete_downloaded_files: bool
    ):
        """删除任务"""
        async with self._schedule_lock:
            if task.id in self.downloading_tasks:
                await self._converge_running_task_locked(
                    task_id=task.id,
                    action="cancel",
                    move_to_pending=False,
                )
            self.pending_tasks.pop(task.id, None)
            if delete_cache:
                with contextlib.suppress(FileNotFoundError):
                    await task.clean_cache()
            if delete_downloaded_files:
                with contextlib.suppress(FileNotFoundError, ValueError):
                    shutil.rmtree(task.download_path)
            await task.delete()
            await self._schedule_tasks_locked()


task_manager = TaskManager()

import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sse_starlette import EventSourceResponse, JSONServerSentEvent
from tortoise.exceptions import DoesNotExist

from app.api.deps import get_task_manager
from app.interfaces.task import TaskStatus
from app.models import Task
from app.schemas.response import ResponsePaginationSchema, ResponseSchema
from app.schemas.tasks import (
    TaskCreatePydantic,
    TaskDeletePydantic,
    TaskPydantic,
    TaskUpdatePydantic,
)
from app.services.task_manager import TaskManager
from app.utils.filters import apply_filters, apply_ordering, pagination

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get(path="/", response_model=ResponsePaginationSchema[TaskPydantic])
async def get_tasks(request: Request):
    queryset = await apply_filters(Task, request)
    queryset = await apply_ordering(queryset, request)
    return await pagination.get_paginated_response_schema(
        queryset, request, TaskPydantic
    )


@router.get("/{task_id:uuid}", response_model=ResponseSchema[TaskPydantic])
async def get_task(task_id: uuid.UUID):
    try:
        task = await Task.get(id=task_id)
        return ResponseSchema(data=await TaskPydantic.from_tortoise_orm(task))
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Task not found")


@router.get("/progress")
async def get_progress(
    request: Request, task_manager: TaskManager = Depends(get_task_manager)
):
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            tasks = task_manager.get_tasks()
            managed_task_ids = {task.id for task in tasks}
            terminated_tasks = await Task.filter(
                status__in=[TaskStatus.STOPPED, TaskStatus.FAILED]
            ).all()
            tasks.extend(
                terminated_task
                for terminated_task in terminated_tasks
                if terminated_task.id not in managed_task_ids
            )
            tasks.sort(key=lambda task: task.created_at)
            data = [
                TaskPydantic.model_validate(task, from_attributes=True).model_dump(
                    mode="json"
                )
                for task in tasks
            ]
            yield JSONServerSentEvent(data=data)
            await asyncio.sleep(1)

    return EventSourceResponse(event_generator())


@router.post("/", response_model=ResponseSchema[TaskPydantic])
async def create_task(
    data: TaskCreatePydantic, task_manager: TaskManager = Depends(get_task_manager)
):
    task = await Task.create(**data.model_dump())
    await task_manager.append_task(task)
    return ResponseSchema(data=await TaskPydantic.from_tortoise_orm(task))


@router.post(
    "/{task_id:uuid}/start",
    response_model=ResponseSchema,
    description="开始暂停、失败的任务",
)
async def start_task(
    task_id: uuid.UUID, task_manager: TaskManager = Depends(get_task_manager)
):
    try:
        task = await Task.get(id=task_id)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status not in {TaskStatus.STOPPED, TaskStatus.FAILED}:
        raise HTTPException(status_code=400, detail="Task is not stopped or failed")
    # 设置任务状态为等待中
    task.status = TaskStatus.PENDING
    await task.save(update_fields=["status"])
    await task_manager.append_task(task)
    return ResponseSchema()


@router.post("/{task_id:uuid}/stop", response_model=ResponseSchema)
async def stop_task(
    task_id: uuid.UUID, task_manager: TaskManager = Depends(get_task_manager)
):
    try:
        task = await Task.get(id=task_id)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Task not found")
    await task_manager.stop_task(task)
    return ResponseSchema()


@router.delete("/{task_id:uuid}", response_model=ResponseSchema)
async def delete_task(
    task_id: uuid.UUID,
    data: TaskDeletePydantic,
    task_manager: TaskManager = Depends(get_task_manager),
):
    try:
        task = await Task.get(id=task_id)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Task not found")
    await task_manager.remove_task(
        task, data.delete_cache, data.delete_downloaded_files
    )
    return ResponseSchema()


@router.put("/{task_id:uuid}", response_model=ResponseSchema)
async def update_task_config(
    task_id: uuid.UUID,
    data: TaskUpdatePydantic,
    task_manager: TaskManager = Depends(get_task_manager),
):
    try:
        # 先从内存中获取任务
        task = task_manager.get_task_by_id(task_id)
        if not task:
            # 如果内存中没有任务，则从数据库中获取
            task = await Task.get(id=task_id)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Task not found")
    # 检查任务状态
    if task.status not in {TaskStatus.STOPPED, TaskStatus.FAILED}:
        raise HTTPException(status_code=400, detail="Task is not pending or failed")
    # 更新任务配置
    task.update_from_dict(data.model_dump(exclude_unset=True))
    await task.save(update_fields=data.model_dump(exclude_unset=True).keys())
    # 如果任务有下载器，则更新下载器配置
    if task.downloader:
        task.downloader = None
    return ResponseSchema()


@router.post("/{task_id:uuid}/restart", response_model=ResponseSchema)
async def restart_task(
    task_id: uuid.UUID, task_manager: TaskManager = Depends(get_task_manager)
):
    try:
        task = await Task.get(id=task_id)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Task is not completed")
    task.status = TaskStatus.PENDING
    await task.save(update_fields=["status"])
    await task_manager.append_task(task)
    return ResponseSchema()


@router.post("/stop_all", response_model=ResponseSchema)
async def stop_all_tasks(task_manager: TaskManager = Depends(get_task_manager)):
    tasks = task_manager.get_tasks()
    for task in tasks:
        await task_manager.stop_task(task)
    return ResponseSchema()


@router.post("/start_all", response_model=ResponseSchema)
async def start_all_tasks(task_manager: TaskManager = Depends(get_task_manager)):
    tasks = await Task.filter(status__in=[TaskStatus.STOPPED, TaskStatus.FAILED])
    for task in tasks:
        task.status = TaskStatus.PENDING
        await task.save(update_fields=["status"])
        await task_manager.append_task(task)
    return ResponseSchema()

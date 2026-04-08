from fastapi import APIRouter, Depends

from app.api.deps import get_task_manager
from app.models import GlobalConfig
from app.schemas.global_config import GlobalConfigPydantic, GlobalConfigUpdatePydantic
from app.schemas.response import ResponseSchema
from app.services.task_manager import TaskManager

router = APIRouter(prefix="/global_config", tags=["global_config"])


def _resolve_field_default(field) -> object | None:
    """优先使用字段默认值；无默认值时返回 None。"""
    default = getattr(field, "default", None)
    if default is None:
        return None
    return default() if callable(default) else default


@router.get(
    path="/",
    response_model=ResponseSchema[GlobalConfigPydantic],
    summary="获取全局配置",
)
async def get_global_config():
    global_config, _ = await GlobalConfig.get_or_create()
    return ResponseSchema(
        data=await GlobalConfigPydantic.from_tortoise_orm(global_config)
    )


@router.post(
    path="/reset",
    response_model=ResponseSchema[GlobalConfigPydantic],
    summary="重置全局配置",
)
async def reset_global_config(task_manager: TaskManager = Depends(get_task_manager)):
    global_config, _ = await GlobalConfig.get_or_create()
    reset_data: dict[str, object | None] = {}
    for field_name, field in global_config._meta.fields_map.items():
        if getattr(field, "pk", False):
            continue
        reset_data[field_name] = _resolve_field_default(field)

    global_config.update_from_dict(reset_data)
    await global_config.save()
    await task_manager.update_task_concurrency(global_config.task_concurrency)
    return ResponseSchema(
        data=await GlobalConfigPydantic.from_tortoise_orm(global_config)
    )


@router.patch(
    path="/",
    response_model=ResponseSchema[GlobalConfigPydantic],
    summary="更新全局配置",
)
async def update_global_config(
    data: GlobalConfigUpdatePydantic,
    task_manager: TaskManager = Depends(get_task_manager),
):  # pyright: ignore[reportInvalidTypeForm]
    global_config, _ = await GlobalConfig.get_or_create()
    global_config.update_from_dict(data.model_dump(exclude_unset=True))
    await global_config.save()
    await task_manager.update_task_concurrency(global_config.task_concurrency)
    return ResponseSchema(
        data=await GlobalConfigPydantic.from_tortoise_orm(global_config)
    )

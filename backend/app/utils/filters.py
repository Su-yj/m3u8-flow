from functools import cached_property
from typing import Type

from fastapi import HTTPException, Request
from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    ValidationInfo,
    computed_field,
    field_validator,
)
from tortoise.contrib.pydantic import PydanticModel
from tortoise.models import Model
from tortoise.queryset import QuerySet

from app.schemas.response import ResponsePaginationSchema


async def apply_filters(
    model: Type[Model],
    request: Request,
    exclude_fields: list[str] | None = None,
):
    """
    通用筛选器：自动匹配 query_params 与 model 字段
    支持 Django 风格的操作符，如: ?name__icontains=admin&age__gte=18
    """
    exclude_fields = exclude_fields or []
    # 1. 获取模型定义的所有合法字段名（包括定义在类中的字段）
    model_fields = model._meta.fields_map.keys()

    filters = {}

    # 2. 遍历请求中的所有查询参数
    for key, value in request.query_params.items():
        # 处理 Django 风格的操作符 (例如 age__gte)
        # 我们取双下划线前的部分作为基础字段名进行校验
        base_field = key.split("__")[0]

        if base_field in exclude_fields:
            continue

        if base_field in model_fields and value:
            # 如果字段存在，将其加入过滤字典
            # 这里简单处理：空字符串不参与过滤
            filters[key] = value

    # 3. 返回过滤后的 QuerySet
    return model.filter(**filters)


async def apply_ordering(
    queryset: QuerySet[Model],
    request: Request,
    ordering_query_param: str = "ordering",
    default_ordering: str | list[str] | None = None,
):
    """
    通用排序器：自动匹配 query_params 与 model 字段
    支持 Django 风格的操作符，如: ?ordering=-name,age

    :param queryset: 查询集
    :param request: 请求
    :param ordering_query_param: 排序查询参数
    :param default_ordering: 默认排序，如: ["-name", "age"] 或 "-name"
    :return: 排序后的查询集
    """
    ordering = request.query_params.get(ordering_query_param)
    if ordering:
        return queryset.order_by(*ordering.split(","))
    if default_ordering:
        if isinstance(default_ordering, str):
            default_ordering = [default_ordering]
        return queryset.order_by(*default_ordering)
    return queryset


class PaginationQuery(BaseModel):
    page: int = Field(default=1, ge=1, title="页码", description="页码，1 表示第一页")
    page_size: int = Field(
        default=10, ge=0, title="每页数量", description="每页数量，0 表示不分页"
    )

    @field_validator("page_size")
    @classmethod
    def clamp_page_size(cls, v: int, info: ValidationInfo):
        max_page_size = (info.context or {}).get("max_page_size")
        return min(v, max_page_size) if max_page_size else v

    @computed_field
    @cached_property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @computed_field
    @cached_property
    def limit(self) -> int:
        return self.page_size

    @computed_field
    @cached_property
    def should_paginate(self) -> bool:
        return self.page_size > 0


async def apply_pagination(
    queryset: QuerySet[Model],
    request: Request,
    page_query_param: str = "page",
    page_size_query_param: str = "page_size",
    default_page_size: int = 10,
    max_page_size: int | None = None,
):
    """
    通用分页器：自动匹配 query_params 与 model 字段
    支持 Django 风格的操作符，如: ?page=1&page_size=10

    :param queryset: 查询集
    :param request: 请求
    :param page_query_param: 页码查询参数
    :param page_size_query_param: 每页数量查询参数
    :param default_page_size: 默认每页数量
    :param max_page_size: 最大每页数量
    :return: 分页后的查询集
    """
    raw = {
        "page": request.query_params.get(page_query_param) or 1,
        "page_size": request.query_params.get(page_size_query_param)
        or default_page_size,
    }
    try:
        pagination_query = PaginationQuery.model_validate(
            raw, context={"max_page_size": max_page_size}
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    if pagination_query.should_paginate:
        return queryset.offset(pagination_query.offset).limit(pagination_query.limit)
    return queryset


class PageNumberPagination:
    page_size: int = 10
    page_query_param: str = "page"
    page_size_query_param: str = "page_size"
    max_page_size: int | None = None

    @staticmethod
    def _positive_int(
        integer_string: str, strict: bool = False, cutoff: int | None = None
    ) -> int:
        """
        将字符串转换为严格正整数。

        :param integer_string: 字符串
        :param strict: 是否严格
        :param cutoff: 截断值
        :return: 整数
        """
        ret = int(integer_string)
        if ret < 0 or (ret == 0 and strict):
            raise ValueError()
        if cutoff:
            return min(ret, cutoff)
        return ret

    def get_page_number(self, request: Request) -> int:
        page_number = request.query_params.get(self.page_query_param, 1)
        try:
            return self._positive_int(str(page_number), strict=True)
        except ValueError:
            return 1

    def get_page_size(self, request: Request) -> int:
        if self.page_size_query_param:
            try:
                return self._positive_int(
                    request.query_params[self.page_size_query_param],
                    strict=True,
                    cutoff=self.max_page_size,
                )
            except (KeyError, ValueError):
                pass

        return self.page_size

    async def get_paginated_response_schema(
        self,
        queryset: QuerySet[Model],
        request: Request,
        schema: type[PydanticModel],
    ) -> ResponsePaginationSchema[PydanticModel]:
        total = await queryset.count()
        page_size = self.get_page_size(request)
        page_number = self.get_page_number(request)
        if page_size > 0:
            queryset = queryset.offset((page_number - 1) * page_size).limit(page_size)
        return ResponsePaginationSchema(
            total=total,
            total_pages=(total + page_size - 1) // page_size if page_size > 0 else 1,
            data=await schema.from_queryset(queryset),
        )


pagination = PageNumberPagination()

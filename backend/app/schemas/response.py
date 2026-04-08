from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseSchema(BaseModel, Generic[T]):
    code: int = 0
    message: str = "OK"
    data: Optional[T] = None

    class Config:
        arbitrary_types_allowed = True


class ResponsePaginationSchema(ResponseSchema[T]):
    total: int
    total_pages: int
    data: list[T] = Field(default_factory=list)

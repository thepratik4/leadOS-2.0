from typing import Generic, TypeVar

from pydantic import BaseModel

DataT = TypeVar("DataT")


class APIErrorDetail(BaseModel):
    code: str
    message: str
    field: str | None = None


class APIErrorResponse(BaseModel):
    success: bool = False
    error: APIErrorDetail


class StandardResponse(BaseModel, Generic[DataT]):
    success: bool = True
    data: DataT
    message: str | None = None

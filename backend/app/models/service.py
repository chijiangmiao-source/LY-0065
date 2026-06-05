from datetime import datetime
from beanie import Document
from pydantic import Field, BaseModel
from typing import Optional, List


class Service(Document):
    service_id: str = Field(..., description="服务编号", unique=True, index=True)
    name: str = Field(..., description="服务名称", index=True)
    duration: int = Field(..., description="服务时长(分钟)")
    price: float = Field(..., description="服务价格")
    description: Optional[str] = Field(None, description="服务描述")
    status: str = Field(default="启用", description="状态")
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "services"
        indexes = [
            [("service_id", 1)],
            [("name", 1)],
        ]


class ServiceCreate(BaseModel):
    service_id: str
    name: str
    duration: int
    price: float
    description: Optional[str] = None
    status: Optional[str] = "启用"


class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    duration: Optional[int] = None
    price: Optional[float] = None
    description: Optional[str] = None
    status: Optional[str] = None


class ServiceResponse(BaseModel):
    id: str
    service_id: str
    name: str
    duration: int
    price: float
    description: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

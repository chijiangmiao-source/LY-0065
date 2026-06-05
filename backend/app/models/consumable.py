from datetime import datetime
from beanie import Document
from pydantic import Field, BaseModel, computed_field
from typing import Optional, List


def get_stock_status(stock_quantity: int) -> str:
    if stock_quantity <= 0:
        return "缺货"
    elif stock_quantity < 10:
        return "库存不足"
    return "正常"


class Consumable(Document):
    consumable_no: str = Field(..., description="耗材编号", unique=True, index=True)
    name: str = Field(..., description="耗材名称", index=True)
    stock_quantity: int = Field(..., description="库存数量")
    applicable_services: List[str] = Field(default_factory=list, description="适用服务项目")
    unit: str = Field(default="个", description="单位")
    status: str = Field(default="正常", description="业务状态(正常/停用)")
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "consumables"
        indexes = [
            [("consumable_no", 1)],
            [("name", 1)],
        ]


class ConsumableCreate(BaseModel):
    consumable_no: str
    name: str
    stock_quantity: int
    applicable_services: Optional[List[str]] = None
    unit: Optional[str] = "个"
    status: Optional[str] = "正常"


class ConsumableUpdate(BaseModel):
    name: Optional[str] = None
    stock_quantity: Optional[int] = None
    applicable_services: Optional[List[str]] = None
    unit: Optional[str] = None
    status: Optional[str] = None


class ConsumableResponse(BaseModel):
    id: str
    consumable_no: str
    name: str
    stock_quantity: int
    applicable_services: List[str]
    unit: str
    status: str
    stock_status: str
    created_at: datetime

    class Config:
        from_attributes = True

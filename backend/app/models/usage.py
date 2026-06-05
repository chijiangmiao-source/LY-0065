from datetime import datetime
from beanie import Document
from pydantic import Field, BaseModel
from typing import Optional


class Usage(Document):
    usage_no: str = Field(..., description="领用编号", unique=True, index=True)
    consumable_no: str = Field(..., description="耗材编号")
    consumable_name: str = Field(..., description="耗材名称")
    quantity: int = Field(..., description="领用数量")
    employee_id: str = Field(..., description="领用人编号")
    employee_name: str = Field(..., description="领用人姓名")
    usage_date: str = Field(..., description="领用日期(YYYY-MM-DD)")
    remark: Optional[str] = Field(None, description="备注")
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "usages"
        indexes = [
            [("usage_no", 1)],
            [("consumable_no", 1)],
            [("usage_date", 1)],
        ]


class UsageCreate(BaseModel):
    usage_no: str
    consumable_no: str
    consumable_name: str
    quantity: int
    employee_id: str
    employee_name: str
    usage_date: str
    remark: Optional[str] = None


class UsageUpdate(BaseModel):
    quantity: Optional[int] = None
    remark: Optional[str] = None


class UsageResponse(BaseModel):
    id: str
    usage_no: str
    consumable_no: str
    consumable_name: str
    quantity: int
    employee_id: str
    employee_name: str
    usage_date: str
    remark: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

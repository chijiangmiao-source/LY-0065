from datetime import datetime
from beanie import Document
from pydantic import Field, BaseModel
from typing import Optional


class MemberLevel(Document):
    level_id: str = Field(..., description="等级编号", unique=True, index=True)
    name: str = Field(..., description="等级名称", unique=True, index=True)
    min_recharge: float = Field(..., description="最低充值金额门槛", ge=0)
    discount_rate: float = Field(..., description="折扣率(0-1之间)，如0.9表示9折", ge=0, le=1)
    description: Optional[str] = Field(None, description="等级描述")
    status: str = Field(default="启用", description="状态")
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "member_levels"
        indexes = [
            [("level_id", 1)],
            [("name", 1)],
        ]


class MemberLevelCreate(BaseModel):
    level_id: str
    name: str
    min_recharge: float
    discount_rate: float
    description: Optional[str] = None
    status: Optional[str] = "启用"


class MemberLevelUpdate(BaseModel):
    name: Optional[str] = None
    min_recharge: Optional[float] = None
    discount_rate: Optional[float] = None
    description: Optional[str] = None
    status: Optional[str] = None


class MemberLevelResponse(BaseModel):
    id: str
    level_id: str
    name: str
    min_recharge: float
    discount_rate: float
    description: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

from datetime import datetime
from beanie import Document
from pydantic import Field, BaseModel
from typing import Optional


class Member(Document):
    member_no: str = Field(..., description="会员编号", unique=True, index=True)
    name: str = Field(..., description="会员姓名", index=True)
    phone: str = Field(..., description="联系电话", unique=True, index=True)
    gender: Optional[str] = Field(None, description="性别")
    level_id: str = Field(..., description="会员等级编号")
    level_name: str = Field(..., description="会员等级名称")
    balance: float = Field(default=0.0, description="储值余额", ge=0)
    total_recharge: float = Field(default=0.0, description="累计充值金额", ge=0)
    total_consumption: float = Field(default=0.0, description="累计消费金额", ge=0)
    remark: Optional[str] = Field(None, description="备注")
    status: str = Field(default="正常", description="状态")
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "members"
        indexes = [
            [("member_no", 1)],
            [("phone", 1)],
            [("name", 1)],
            [("level_id", 1)],
        ]


class MemberCreate(BaseModel):
    member_no: str
    name: str
    phone: str
    gender: Optional[str] = None
    level_id: str
    level_name: str
    balance: Optional[float] = 0.0
    remark: Optional[str] = None
    status: Optional[str] = "正常"


class MemberUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    level_id: Optional[str] = None
    level_name: Optional[str] = None
    remark: Optional[str] = None
    status: Optional[str] = None


class MemberResponse(BaseModel):
    id: str
    member_no: str
    name: str
    phone: str
    gender: Optional[str]
    level_id: str
    level_name: str
    balance: float
    total_recharge: float
    total_consumption: float
    remark: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

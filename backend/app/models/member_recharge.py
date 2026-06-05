from datetime import datetime
from beanie import Document
from pydantic import Field, BaseModel
from typing import Optional


class MemberRecharge(Document):
    recharge_no: str = Field(..., description="充值流水号", unique=True, index=True)
    member_no: str = Field(..., description="会员编号", index=True)
    member_name: str = Field(..., description="会员姓名")
    phone: str = Field(..., description="联系电话")
    recharge_amount: float = Field(..., description="充值金额", gt=0)
    gift_amount: float = Field(default=0.0, description="赠送金额", ge=0)
    total_amount: float = Field(..., description="总增加金额")
    balance_before: float = Field(..., description="充值前余额", ge=0)
    balance_after: float = Field(..., description="充值后余额", ge=0)
    operator: str = Field(..., description="操作人")
    remark: Optional[str] = Field(None, description="备注")
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "member_recharges"
        indexes = [
            [("recharge_no", 1)],
            [("member_no", 1)],
            [("created_at", 1)],
        ]


class MemberRechargeCreate(BaseModel):
    member_no: str
    recharge_amount: float
    gift_amount: Optional[float] = 0.0
    remark: Optional[str] = None


class MemberRechargeResponse(BaseModel):
    id: str
    recharge_no: str
    member_no: str
    member_name: str
    phone: str
    recharge_amount: float
    gift_amount: float
    total_amount: float
    balance_before: float
    balance_after: float
    operator: str
    remark: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

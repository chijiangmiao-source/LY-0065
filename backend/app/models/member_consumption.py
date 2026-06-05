from datetime import datetime
from beanie import Document
from pydantic import Field, BaseModel
from typing import Optional


class MemberConsumption(Document):
    consumption_no: str = Field(..., description="消费流水号", unique=True, index=True)
    member_no: Optional[str] = Field(None, description="会员编号", index=True)
    member_name: Optional[str] = Field(None, description="会员姓名")
    phone: Optional[str] = Field(None, description="联系电话")
    appointment_no: Optional[str] = Field(None, description="关联预约编号", index=True)
    service_id: str = Field(..., description="服务项目编号")
    service_name: str = Field(..., description="服务项目名称")
    original_price: float = Field(..., description="原始价格", ge=0)
    discount_rate: float = Field(default=1.0, description="折扣率")
    actual_amount: float = Field(..., description="实付金额", ge=0)
    pay_method: str = Field(..., description="支付方式(余额/现金)")
    balance_before: Optional[float] = Field(None, description="余额支付前余额", ge=0)
    balance_after: Optional[float] = Field(None, description="余额支付后余额", ge=0)
    operator: str = Field(..., description="操作人")
    remark: Optional[str] = Field(None, description="备注")
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "member_consumptions"
        indexes = [
            [("consumption_no", 1)],
            [("member_no", 1)],
            [("appointment_no", 1)],
            [("created_at", 1)],
        ]


class MemberConsumptionCreate(BaseModel):
    member_no: Optional[str] = None
    appointment_no: Optional[str] = None
    service_id: str
    service_name: str
    original_price: float
    discount_rate: Optional[float] = 1.0
    actual_amount: float
    pay_method: str
    remark: Optional[str] = None


class MemberConsumptionResponse(BaseModel):
    id: str
    consumption_no: str
    member_no: Optional[str]
    member_name: Optional[str]
    phone: Optional[str]
    appointment_no: Optional[str]
    service_id: str
    service_name: str
    original_price: float
    discount_rate: float
    actual_amount: float
    pay_method: str
    balance_before: Optional[float]
    balance_after: Optional[float]
    operator: str
    remark: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

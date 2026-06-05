from datetime import datetime
from beanie import Document
from pydantic import Field, BaseModel
from typing import Optional


class PackageRedemption(Document):
    redemption_no: str = Field(..., description="核销编号", unique=True, index=True)
    member_package_no: str = Field(..., description="会员套餐编号", index=True)
    member_no: str = Field(..., description="会员编号", index=True)
    member_name: str = Field(..., description="会员姓名")
    phone: str = Field(..., description="联系电话")
    package_no: str = Field(..., description="套餐编号")
    package_name: str = Field(..., description="套餐名称")
    appointment_no: Optional[str] = Field(None, description="关联预约编号", index=True)
    service_id: str = Field(..., description="服务项目编号")
    service_name: str = Field(..., description="服务项目名称")
    employee_id: Optional[str] = Field(None, description="服务员工编号")
    employee_name: Optional[str] = Field(None, description="服务员工姓名")
    redeem_times: int = Field(default=1, description="核销次数", gt=0)
    remaining_before: int = Field(..., description="核销前剩余次数", ge=0)
    remaining_after: int = Field(..., description="核销后剩余次数", ge=0)
    mixed_payment: bool = Field(default=False, description="是否混合支付")
    mixed_pay_amount: Optional[float] = Field(None, description="混合支付金额", ge=0)
    operator: str = Field(..., description="操作人")
    remark: Optional[str] = Field(None, description="备注")
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "package_redemptions"
        indexes = [
            [("redemption_no", 1)],
            [("member_package_no", 1)],
            [("member_no", 1)],
            [("appointment_no", 1)],
            [("created_at", 1)],
        ]


class PackageRedemptionResponse(BaseModel):
    id: str
    redemption_no: str
    member_package_no: str
    member_no: str
    member_name: str
    phone: str
    package_no: str
    package_name: str
    appointment_no: Optional[str]
    service_id: str
    service_name: str
    employee_id: Optional[str]
    employee_name: Optional[str]
    redeem_times: int
    remaining_before: int
    remaining_after: int
    mixed_payment: bool
    mixed_pay_amount: Optional[float]
    operator: str
    remark: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

from datetime import datetime, timedelta
from beanie import Document
from pydantic import Field, BaseModel
from typing import Optional


class MemberPackage(Document):
    member_package_no: str = Field(..., description="会员套餐编号", unique=True, index=True)
    member_no: str = Field(..., description="会员编号", index=True)
    member_name: str = Field(..., description="会员姓名")
    phone: str = Field(..., description="联系电话")
    package_no: str = Field(..., description="套餐编号", index=True)
    package_name: str = Field(..., description="套餐名称")
    package_type: str = Field(..., description="套餐类型(次卡/套餐)")
    total_times: int = Field(..., description="总次数", ge=0)
    used_times: int = Field(default=0, description="已使用次数", ge=0)
    remaining_times: int = Field(..., description="剩余次数", ge=0)
    price: float = Field(..., description="套餐价格", ge=0)
    purchase_date: datetime = Field(default_factory=datetime.now, description="购买日期")
    expire_date: datetime = Field(..., description="过期日期")
    applicable_service_ids: list = Field(default_factory=list, description="适用服务项目编号列表")
    applicable_service_names: list = Field(default_factory=list, description="适用服务项目名称列表")
    applicable_employee_ids: list = Field(default_factory=list, description="适用员工编号列表")
    allow_mixed_payment: bool = Field(default=True, description="是否可与余额混合支付")
    status: str = Field(default="生效中", description="状态(生效中/已冻结/已过期/已作废)")
    operator: str = Field(..., description="操作人")
    remark: Optional[str] = Field(None, description="备注")
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "member_packages"
        indexes = [
            [("member_package_no", 1)],
            [("member_no", 1)],
            [("package_no", 1)],
            [("status", 1)],
            [("expire_date", 1)],
        ]


class MemberPackageCreate(BaseModel):
    member_no: str
    package_no: str
    remark: Optional[str] = None


class MemberPackageRenew(BaseModel):
    member_package_no: str
    remark: Optional[str] = None


class MemberPackageStatusUpdate(BaseModel):
    status: str
    remark: Optional[str] = None


class MemberPackageResponse(BaseModel):
    id: str
    member_package_no: str
    member_no: str
    member_name: str
    phone: str
    package_no: str
    package_name: str
    package_type: str
    total_times: int
    used_times: int
    remaining_times: int
    price: float
    purchase_date: datetime
    expire_date: datetime
    applicable_service_ids: list
    applicable_service_names: list
    applicable_employee_ids: list
    allow_mixed_payment: bool
    status: str
    operator: str
    remark: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

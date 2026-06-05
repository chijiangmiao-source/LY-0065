from datetime import datetime, timedelta
from beanie import Document
from pydantic import Field, BaseModel
from typing import Optional, List


class PackageCard(Document):
    package_no: str = Field(..., description="套餐编号", unique=True, index=True)
    name: str = Field(..., description="套餐名称", index=True)
    package_type: str = Field(..., description="套餐类型(次卡/套餐)")
    price: float = Field(..., description="套餐价格", gt=0)
    total_times: int = Field(..., description="总次数", gt=0)
    gift_times: int = Field(default=0, description="赠送次数", ge=0)
    valid_days: int = Field(default=365, description="有效期(天)", gt=0)
    applicable_service_ids: List[str] = Field(default_factory=list, description="适用服务项目编号列表")
    applicable_service_names: List[str] = Field(default_factory=list, description="适用服务项目名称列表")
    applicable_employee_ids: List[str] = Field(default_factory=list, description="适用员工编号列表，空表示全部")
    applicable_store_ids: List[str] = Field(default_factory=list, description="适用门店编号列表，空表示全部")
    allow_mixed_payment: bool = Field(default=True, description="是否可与余额混合支付")
    description: Optional[str] = Field(None, description="套餐描述")
    status: str = Field(default="启用", description="状态(启用/禁用)")
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "package_cards"
        indexes = [
            [("package_no", 1)],
            [("name", 1)],
            [("status", 1)],
        ]


class PackageCardCreate(BaseModel):
    package_no: Optional[str] = None
    name: str
    package_type: str = "次卡"
    price: float
    total_times: int
    gift_times: Optional[int] = 0
    valid_days: Optional[int] = 365
    applicable_service_ids: Optional[List[str]] = []
    applicable_service_names: Optional[List[str]] = []
    applicable_employee_ids: Optional[List[str]] = []
    applicable_store_ids: Optional[List[str]] = []
    allow_mixed_payment: Optional[bool] = True
    description: Optional[str] = None
    status: Optional[str] = "启用"


class PackageCardUpdate(BaseModel):
    name: Optional[str] = None
    package_type: Optional[str] = None
    price: Optional[float] = None
    total_times: Optional[int] = None
    gift_times: Optional[int] = None
    valid_days: Optional[int] = None
    applicable_service_ids: Optional[List[str]] = None
    applicable_service_names: Optional[List[str]] = None
    applicable_employee_ids: Optional[List[str]] = None
    applicable_store_ids: Optional[List[str]] = None
    allow_mixed_payment: Optional[bool] = None
    description: Optional[str] = None
    status: Optional[str] = None


class PackageCardResponse(BaseModel):
    id: str
    package_no: str
    name: str
    package_type: str
    price: float
    total_times: int
    gift_times: int
    valid_days: int
    applicable_service_ids: List[str]
    applicable_service_names: List[str]
    applicable_employee_ids: List[str]
    applicable_store_ids: List[str]
    allow_mixed_payment: bool
    description: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

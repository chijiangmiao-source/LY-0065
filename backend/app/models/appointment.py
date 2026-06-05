from datetime import datetime
from beanie import Document
from pydantic import Field, BaseModel
from typing import Optional


class Appointment(Document):
    appointment_no: str = Field(..., description="预约编号", unique=True, index=True)
    customer_name: str = Field(..., description="客户姓名")
    phone: str = Field(..., description="联系电话")
    service_id: str = Field(..., description="服务项目编号")
    service_name: str = Field(..., description="服务项目名称")
    employee_id: Optional[str] = Field(None, description="员工编号")
    employee_name: Optional[str] = Field(None, description="员工姓名")
    appointment_date: str = Field(..., description="预约日期(YYYY-MM-DD)")
    time_slot: str = Field(..., description="预约时段")
    status: str = Field(default="待服务", description="预约状态")
    pay_method: Optional[str] = Field(None, description="支付方式(余额/现金)")
    member_no: Optional[str] = Field(None, description="关联会员编号")
    pay_amount: Optional[float] = Field(None, description="实付金额")
    discount_rate: Optional[float] = Field(None, description="使用折扣率")
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "appointments"
        indexes = [
            [("appointment_no", 1)],
            [("appointment_date", 1), ("time_slot", 1)],
            [("status", 1)],
            [("member_no", 1)],
        ]


class AppointmentCreate(BaseModel):
    appointment_no: str
    customer_name: str
    phone: str
    service_id: str
    service_name: str
    employee_id: Optional[str] = None
    employee_name: Optional[str] = None
    appointment_date: str
    time_slot: str
    status: Optional[str] = "待服务"


class AppointmentUpdate(BaseModel):
    customer_name: Optional[str] = None
    phone: Optional[str] = None
    service_id: Optional[str] = None
    service_name: Optional[str] = None
    employee_id: Optional[str] = None
    employee_name: Optional[str] = None
    appointment_date: Optional[str] = None
    time_slot: Optional[str] = None
    status: Optional[str] = None


class AppointmentCompleteRequest(BaseModel):
    pay_method: str = Field(..., description="支付方式(余额/现金/次卡)")
    member_no: Optional[str] = Field(None, description="会员编号(余额或次卡支付时必填)")
    member_package_no: Optional[str] = Field(None, description="会员套餐编号(次卡支付时必填)")
    use_mixed_payment: Optional[bool] = Field(False, description="是否使用混合支付(次卡+余额)")


class AppointmentResponse(BaseModel):
    id: str
    appointment_no: str
    customer_name: str
    phone: str
    service_id: str
    service_name: str
    employee_id: Optional[str]
    employee_name: Optional[str]
    appointment_date: str
    time_slot: str
    status: str
    pay_method: Optional[str]
    member_no: Optional[str]
    pay_amount: Optional[float]
    discount_rate: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True

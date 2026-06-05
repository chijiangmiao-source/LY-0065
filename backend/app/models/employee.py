from datetime import datetime
from beanie import Document
from pydantic import Field, BaseModel
from typing import Optional


class Employee(Document):
    employee_id: str = Field(..., description="员工编号", unique=True, index=True)
    name: str = Field(..., description="员工姓名", index=True)
    phone: str = Field(..., description="联系电话")
    position: str = Field(..., description="职位")
    status: str = Field(default="在职", description="状态")
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "employees"
        indexes = [
            [("employee_id", 1)],
            [("name", 1)],
        ]


class EmployeeCreate(BaseModel):
    employee_id: str
    name: str
    phone: str
    position: str
    status: Optional[str] = "在职"


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    status: Optional[str] = None


class EmployeeResponse(BaseModel):
    id: str
    employee_id: str
    name: str
    phone: str
    position: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

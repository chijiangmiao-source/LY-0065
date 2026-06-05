from datetime import datetime
from beanie import Document
from pydantic import Field, BaseModel
from typing import Optional


class Schedule(Document):
    schedule_id: str = Field(..., description="排班编号", unique=True, index=True)
    employee_id: str = Field(..., description="员工编号", index=True)
    employee_name: str = Field(..., description="员工姓名")
    schedule_date: str = Field(..., description="排班日期(YYYY-MM-DD)")
    time_slot: str = Field(..., description="排班时段")
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "schedules"
        indexes = [
            [("schedule_id", 1)],
            [("employee_id", 1), ("schedule_date", 1), ("time_slot", 1)],
        ]


class ScheduleCreate(BaseModel):
    schedule_id: str
    employee_id: str
    employee_name: str
    schedule_date: str
    time_slot: str


class ScheduleUpdate(BaseModel):
    schedule_date: Optional[str] = None
    time_slot: Optional[str] = None


class ScheduleResponse(BaseModel):
    id: str
    schedule_id: str
    employee_id: str
    employee_name: str
    schedule_date: str
    time_slot: str
    created_at: datetime

    class Config:
        from_attributes = True

from datetime import datetime
from beanie import Document
from pydantic import Field, BaseModel
from typing import Optional, Any


class OperationLog(Document):
    log_id: str = Field(..., description="日志编号", unique=True, index=True)
    operator: str = Field(..., description="操作人", index=True)
    module: str = Field(..., description="操作模块", index=True)
    action: str = Field(..., description="操作类型")
    target_id: Optional[str] = Field(None, description="目标对象ID/编号")
    detail: Optional[str] = Field(None, description="操作详情")
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "operation_logs"
        indexes = [
            [("log_id", 1)],
            [("operator", 1)],
            [("module", 1)],
            [("created_at", 1)],
        ]


class OperationLogResponse(BaseModel):
    id: str
    log_id: str
    operator: str
    module: str
    action: str
    target_id: Optional[str]
    detail: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

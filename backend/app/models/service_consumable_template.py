from datetime import datetime
from beanie import Document
from pydantic import Field, BaseModel
from typing import Optional, List


class ServiceConsumableTemplate(Document):
    template_id: str = Field(..., description="模板编号", unique=True, index=True)
    service_id: str = Field(..., description="服务项目编号", index=True)
    service_name: str = Field(..., description="服务项目名称")
    items: List[dict] = Field(default_factory=list, description="耗材清单 [{consumable_no, consumable_name, quantity, unit}]")
    remark: Optional[str] = Field(None, description="备注")
    status: str = Field(default="启用", description="状态(启用/停用)")
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "service_consumable_templates"
        indexes = [
            [("template_id", 1)],
            [("service_id", 1)],
        ]


class TemplateItem(BaseModel):
    consumable_no: str
    consumable_name: str
    quantity: int
    unit: str = "个"


class ServiceConsumableTemplateCreate(BaseModel):
    template_id: str
    service_id: str
    service_name: str
    items: List[TemplateItem]
    remark: Optional[str] = None
    status: Optional[str] = "启用"


class ServiceConsumableTemplateUpdate(BaseModel):
    service_id: Optional[str] = None
    service_name: Optional[str] = None
    items: Optional[List[TemplateItem]] = None
    remark: Optional[str] = None
    status: Optional[str] = None


class ServiceConsumableTemplateResponse(BaseModel):
    id: str
    template_id: str
    service_id: str
    service_name: str
    items: List[dict]
    remark: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

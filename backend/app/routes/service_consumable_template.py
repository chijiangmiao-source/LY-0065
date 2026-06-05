from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from app.models.service_consumable_template import (
    ServiceConsumableTemplate,
    ServiceConsumableTemplateCreate,
    ServiceConsumableTemplateUpdate,
    ServiceConsumableTemplateResponse,
)
from app.models.service import Service
from app.models.consumable import Consumable
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter()


def build_template_response(t: ServiceConsumableTemplate) -> ServiceConsumableTemplateResponse:
    return ServiceConsumableTemplateResponse(
        id=str(t.id),
        template_id=t.template_id,
        service_id=t.service_id,
        service_name=t.service_name,
        items=t.items,
        remark=t.remark,
        status=t.status,
        created_at=t.created_at
    )


@router.post("", response_model=ServiceConsumableTemplateResponse)
async def create_template(template: ServiceConsumableTemplateCreate, current_user: User = Depends(get_current_user)):
    existing = await ServiceConsumableTemplate.find_one(ServiceConsumableTemplate.template_id == template.template_id)
    if existing:
        raise HTTPException(status_code=400, detail="模板编号已存在")

    service = await Service.find_one(Service.service_id == template.service_id)
    if not service:
        raise HTTPException(status_code=400, detail="服务项目不存在")

    for item in template.items:
        if item.quantity <= 0:
            raise HTTPException(status_code=400, detail=f"耗材 {item.consumable_name} 的用量必须大于0")
        consumable = await Consumable.find_one(Consumable.consumable_no == item.consumable_no)
        if not consumable:
            raise HTTPException(status_code=400, detail=f"耗材 {item.consumable_no} 不存在")

    items_dict = [item.model_dump() for item in template.items]
    db_template = ServiceConsumableTemplate(
        template_id=template.template_id,
        service_id=template.service_id,
        service_name=template.service_name,
        items=items_dict,
        remark=template.remark,
        status=template.status or "启用"
    )
    await db_template.insert()
    return build_template_response(db_template)


@router.get("", response_model=List[ServiceConsumableTemplateResponse])
async def get_templates(
    service_id: Optional[str] = Query(None, description="服务项目编号"),
    service_name: Optional[str] = Query(None, description="服务项目名称"),
    status: Optional[str] = Query(None, description="状态"),
    current_user: User = Depends(get_current_user)
):
    query = {}
    if service_id:
        query["service_id"] = service_id
    if service_name:
        query["service_name"] = {"$regex": service_name, "$options": "i"}
    if status:
        query["status"] = status

    templates = await ServiceConsumableTemplate.find(query).sort("-created_at").to_list()
    return [build_template_response(t) for t in templates]


@router.get("/{template_id}", response_model=ServiceConsumableTemplateResponse)
async def get_template(template_id: str, current_user: User = Depends(get_current_user)):
    template = await ServiceConsumableTemplate.find_one(ServiceConsumableTemplate.template_id == template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return build_template_response(template)


@router.get("/service/{service_id}", response_model=ServiceConsumableTemplateResponse)
async def get_template_by_service(service_id: str, current_user: User = Depends(get_current_user)):
    template = await ServiceConsumableTemplate.find_one(
        ServiceConsumableTemplate.service_id == service_id,
        ServiceConsumableTemplate.status == "启用"
    )
    if not template:
        raise HTTPException(status_code=404, detail="该服务项目未配置耗材模板")
    return build_template_response(template)


@router.put("/{template_id}", response_model=ServiceConsumableTemplateResponse)
async def update_template(template_id: str, template_update: ServiceConsumableTemplateUpdate, current_user: User = Depends(get_current_user)):
    template = await ServiceConsumableTemplate.find_one(ServiceConsumableTemplate.template_id == template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    update_data = template_update.model_dump(exclude_unset=True)

    if "items" in update_data:
        for item in update_data["items"]:
            if item["quantity"] <= 0:
                raise HTTPException(status_code=400, detail=f"耗材 {item['consumable_name']} 的用量必须大于0")
            consumable = await Consumable.find_one(Consumable.consumable_no == item["consumable_no"])
            if not consumable:
                raise HTTPException(status_code=400, detail=f"耗材 {item['consumable_no']} 不存在")
        update_data["items"] = [item.model_dump() if hasattr(item, 'model_dump') else item for item in update_data["items"]]

    if "service_id" in update_data:
        service = await Service.find_one(Service.service_id == update_data["service_id"])
        if not service:
            raise HTTPException(status_code=400, detail="服务项目不存在")

    for key, value in update_data.items():
        setattr(template, key, value)

    await template.save()
    return build_template_response(template)


@router.delete("/{template_id}")
async def delete_template(template_id: str, current_user: User = Depends(get_current_user)):
    template = await ServiceConsumableTemplate.find_one(ServiceConsumableTemplate.template_id == template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    await template.delete()
    return {"message": "删除成功"}

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from app.models.service import Service, ServiceCreate, ServiceUpdate, ServiceResponse
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter()


@router.post("", response_model=ServiceResponse)
async def create_service(service: ServiceCreate, current_user: User = Depends(get_current_user)):
    existing = await Service.find_one(Service.service_id == service.service_id)
    if existing:
        raise HTTPException(status_code=400, detail="服务编号已存在")
    db_service = Service(**service.model_dump())
    await db_service.insert()
    return ServiceResponse(
        id=str(db_service.id),
        service_id=db_service.service_id,
        name=db_service.name,
        duration=db_service.duration,
        price=db_service.price,
        description=db_service.description,
        status=db_service.status,
        created_at=db_service.created_at
    )


@router.get("", response_model=List[ServiceResponse])
async def get_services(
    name: Optional[str] = Query(None, description="服务名称"),
    status: Optional[str] = Query(None, description="状态"),
    current_user: User = Depends(get_current_user)
):
    query = {}
    if name:
        query["name"] = {"$regex": name, "$options": "i"}
    if status:
        query["status"] = status
    
    services = await Service.find(query).to_list()
    return [
        ServiceResponse(
            id=str(s.id),
            service_id=s.service_id,
            name=s.name,
            duration=s.duration,
            price=s.price,
            description=s.description,
            status=s.status,
            created_at=s.created_at
        ) for s in services
    ]


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(service_id: str, current_user: User = Depends(get_current_user)):
    service = await Service.find_one(Service.service_id == service_id)
    if not service:
        raise HTTPException(status_code=404, detail="服务不存在")
    return ServiceResponse(
        id=str(service.id),
        service_id=service.service_id,
        name=service.name,
        duration=service.duration,
        price=service.price,
        description=service.description,
        status=service.status,
        created_at=service.created_at
    )


@router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(service_id: str, service_update: ServiceUpdate, current_user: User = Depends(get_current_user)):
    service = await Service.find_one(Service.service_id == service_id)
    if not service:
        raise HTTPException(status_code=404, detail="服务不存在")
    
    update_data = service_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(service, key, value)
    
    await service.save()
    return ServiceResponse(
        id=str(service.id),
        service_id=service.service_id,
        name=service.name,
        duration=service.duration,
        price=service.price,
        description=service.description,
        status=service.status,
        created_at=service.created_at
    )


@router.delete("/{service_id}")
async def delete_service(service_id: str, current_user: User = Depends(get_current_user)):
    service = await Service.find_one(Service.service_id == service_id)
    if not service:
        raise HTTPException(status_code=404, detail="服务不存在")
    await service.delete()
    return {"message": "删除成功"}

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from app.models.usage import Usage, UsageCreate, UsageUpdate, UsageResponse
from app.models.consumable import Consumable
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter()


@router.post("", response_model=UsageResponse)
async def create_usage(usage: UsageCreate, current_user: User = Depends(get_current_user)):
    existing = await Usage.find_one(Usage.usage_no == usage.usage_no)
    if existing:
        raise HTTPException(status_code=400, detail="领用编号已存在")
    
    consumable = await Consumable.find_one(Consumable.consumable_no == usage.consumable_no)
    if not consumable:
        raise HTTPException(status_code=400, detail="耗材不存在")
    
    if usage.quantity > consumable.stock_quantity:
        raise HTTPException(status_code=400, detail=f"领用数量不能超过耗材库存，当前库存: {consumable.stock_quantity}")
    
    if usage.quantity <= 0:
        raise HTTPException(status_code=400, detail="领用数量必须大于0")
    
    consumable.stock_quantity -= usage.quantity
    await consumable.save()
    
    db_usage = Usage(**usage.model_dump())
    await db_usage.insert()
    return UsageResponse(
        id=str(db_usage.id),
        usage_no=db_usage.usage_no,
        consumable_no=db_usage.consumable_no,
        consumable_name=db_usage.consumable_name,
        quantity=db_usage.quantity,
        employee_id=db_usage.employee_id,
        employee_name=db_usage.employee_name,
        usage_date=db_usage.usage_date,
        remark=db_usage.remark,
        created_at=db_usage.created_at
    )


@router.get("", response_model=List[UsageResponse])
async def get_usages(
    consumable_no: Optional[str] = Query(None, description="耗材编号"),
    consumable_name: Optional[str] = Query(None, description="耗材名称"),
    employee_id: Optional[str] = Query(None, description="员工编号"),
    usage_date: Optional[str] = Query(None, description="领用日期"),
    current_user: User = Depends(get_current_user)
):
    query = {}
    if consumable_no:
        query["consumable_no"] = consumable_no
    if consumable_name:
        query["consumable_name"] = {"$regex": consumable_name, "$options": "i"}
    if employee_id:
        query["employee_id"] = employee_id
    if usage_date:
        query["usage_date"] = usage_date
    
    usages = await Usage.find(query).sort("-created_at").to_list()
    return [
        UsageResponse(
            id=str(u.id),
            usage_no=u.usage_no,
            consumable_no=u.consumable_no,
            consumable_name=u.consumable_name,
            quantity=u.quantity,
            employee_id=u.employee_id,
            employee_name=u.employee_name,
            usage_date=u.usage_date,
            remark=u.remark,
            created_at=u.created_at
        ) for u in usages
    ]


@router.get("/{usage_no}", response_model=UsageResponse)
async def get_usage(usage_no: str, current_user: User = Depends(get_current_user)):
    usage = await Usage.find_one(Usage.usage_no == usage_no)
    if not usage:
        raise HTTPException(status_code=404, detail="领用记录不存在")
    return UsageResponse(
        id=str(usage.id),
        usage_no=usage.usage_no,
        consumable_no=usage.consumable_no,
        consumable_name=usage.consumable_name,
        quantity=usage.quantity,
        employee_id=usage.employee_id,
        employee_name=usage.employee_name,
        usage_date=usage.usage_date,
        remark=usage.remark,
        created_at=usage.created_at
    )


@router.delete("/{usage_no}")
async def delete_usage(usage_no: str, current_user: User = Depends(get_current_user)):
    usage = await Usage.find_one(Usage.usage_no == usage_no)
    if not usage:
        raise HTTPException(status_code=404, detail="领用记录不存在")
    
    consumable = await Consumable.find_one(Consumable.consumable_no == usage.consumable_no)
    if consumable:
        consumable.stock_quantity += usage.quantity
        await consumable.save()
    
    await usage.delete()
    return {"message": "删除成功，库存已退还"}

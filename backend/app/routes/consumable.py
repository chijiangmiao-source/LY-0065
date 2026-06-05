from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from app.models.consumable import Consumable, ConsumableCreate, ConsumableUpdate, ConsumableResponse, get_stock_status
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter()


def build_consumable_response(c: Consumable) -> ConsumableResponse:
    return ConsumableResponse(
        id=str(c.id),
        consumable_no=c.consumable_no,
        name=c.name,
        stock_quantity=c.stock_quantity,
        warning_threshold=c.warning_threshold,
        applicable_services=c.applicable_services,
        unit=c.unit,
        status=c.status,
        stock_status=get_stock_status(c.stock_quantity, c.warning_threshold),
        created_at=c.created_at
    )


@router.post("", response_model=ConsumableResponse)
async def create_consumable(consumable: ConsumableCreate, current_user: User = Depends(get_current_user)):
    existing = await Consumable.find_one(Consumable.consumable_no == consumable.consumable_no)
    if existing:
        raise HTTPException(status_code=400, detail="耗材编号已存在")
    db_consumable = Consumable(**consumable.model_dump())
    await db_consumable.insert()
    return build_consumable_response(db_consumable)


@router.get("", response_model=List[ConsumableResponse])
async def get_consumables(
    name: Optional[str] = Query(None, description="耗材名称"),
    status: Optional[str] = Query(None, description="业务状态(正常/停用)"),
    current_user: User = Depends(get_current_user)
):
    query = {}
    if name:
        query["name"] = {"$regex": name, "$options": "i"}
    if status:
        query["status"] = status
    
    consumables = await Consumable.find(query).to_list()
    return [build_consumable_response(c) for c in consumables]


@router.get("/{consumable_no}", response_model=ConsumableResponse)
async def get_consumable(consumable_no: str, current_user: User = Depends(get_current_user)):
    consumable = await Consumable.find_one(Consumable.consumable_no == consumable_no)
    if not consumable:
        raise HTTPException(status_code=404, detail="耗材不存在")
    return build_consumable_response(consumable)


@router.put("/{consumable_no}", response_model=ConsumableResponse)
async def update_consumable(consumable_no: str, consumable_update: ConsumableUpdate, current_user: User = Depends(get_current_user)):
    consumable = await Consumable.find_one(Consumable.consumable_no == consumable_no)
    if not consumable:
        raise HTTPException(status_code=404, detail="耗材不存在")
    
    update_data = consumable_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(consumable, key, value)
    
    await consumable.save()
    return build_consumable_response(consumable)


@router.delete("/{consumable_no}")
async def delete_consumable(consumable_no: str, current_user: User = Depends(get_current_user)):
    consumable = await Consumable.find_one(Consumable.consumable_no == consumable_no)
    if not consumable:
        raise HTTPException(status_code=404, detail="耗材不存在")
    await consumable.delete()
    return {"message": "删除成功"}


@router.post("/{consumable_no}/stock/add")
async def add_stock(consumable_no: str, quantity: int, current_user: User = Depends(get_current_user)):
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="入库数量必须大于0")
    consumable = await Consumable.find_one(Consumable.consumable_no == consumable_no)
    if not consumable:
        raise HTTPException(status_code=404, detail="耗材不存在")
    consumable.stock_quantity += quantity
    await consumable.save()
    return {"message": f"入库成功，当前库存: {consumable.stock_quantity}"}

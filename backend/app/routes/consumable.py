from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from app.models.consumable import Consumable, ConsumableCreate, ConsumableUpdate, ConsumableResponse
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter()


@router.post("", response_model=ConsumableResponse)
async def create_consumable(consumable: ConsumableCreate, current_user: User = Depends(get_current_user)):
    existing = await Consumable.find_one(Consumable.consumable_no == consumable.consumable_no)
    if existing:
        raise HTTPException(status_code=400, detail="耗材编号已存在")
    db_consumable = Consumable(**consumable.model_dump())
    await db_consumable.insert()
    return ConsumableResponse(
        id=str(db_consumable.id),
        consumable_no=db_consumable.consumable_no,
        name=db_consumable.name,
        stock_quantity=db_consumable.stock_quantity,
        applicable_services=db_consumable.applicable_services,
        unit=db_consumable.unit,
        status=db_consumable.status,
        created_at=db_consumable.created_at
    )


@router.get("", response_model=List[ConsumableResponse])
async def get_consumables(
    name: Optional[str] = Query(None, description="耗材名称"),
    status: Optional[str] = Query(None, description="状态"),
    current_user: User = Depends(get_current_user)
):
    query = {}
    if name:
        query["name"] = {"$regex": name, "$options": "i"}
    if status:
        query["status"] = status
    
    consumables = await Consumable.find(query).to_list()
    return [
        ConsumableResponse(
            id=str(c.id),
            consumable_no=c.consumable_no,
            name=c.name,
            stock_quantity=c.stock_quantity,
            applicable_services=c.applicable_services,
            unit=c.unit,
            status=c.status,
            created_at=c.created_at
        ) for c in consumables
    ]


@router.get("/{consumable_no}", response_model=ConsumableResponse)
async def get_consumable(consumable_no: str, current_user: User = Depends(get_current_user)):
    consumable = await Consumable.find_one(Consumable.consumable_no == consumable_no)
    if not consumable:
        raise HTTPException(status_code=404, detail="耗材不存在")
    return ConsumableResponse(
        id=str(consumable.id),
        consumable_no=consumable.consumable_no,
        name=consumable.name,
        stock_quantity=consumable.stock_quantity,
        applicable_services=consumable.applicable_services,
        unit=consumable.unit,
        status=consumable.status,
        created_at=consumable.created_at
    )


@router.put("/{consumable_no}", response_model=ConsumableResponse)
async def update_consumable(consumable_no: str, consumable_update: ConsumableUpdate, current_user: User = Depends(get_current_user)):
    consumable = await Consumable.find_one(Consumable.consumable_no == consumable_no)
    if not consumable:
        raise HTTPException(status_code=404, detail="耗材不存在")
    
    update_data = consumable_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(consumable, key, value)
    
    await consumable.save()
    return ConsumableResponse(
        id=str(consumable.id),
        consumable_no=consumable.consumable_no,
        name=consumable.name,
        stock_quantity=consumable.stock_quantity,
        applicable_services=consumable.applicable_services,
        unit=consumable.unit,
        status=consumable.status,
        created_at=consumable.created_at
    )


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

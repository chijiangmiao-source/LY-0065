from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from app.models.schedule import Schedule, ScheduleCreate, ScheduleUpdate, ScheduleResponse
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter()


@router.post("", response_model=ScheduleResponse)
async def create_schedule(schedule: ScheduleCreate, current_user: User = Depends(get_current_user)):
    existing_id = await Schedule.find_one(Schedule.schedule_id == schedule.schedule_id)
    if existing_id:
        raise HTTPException(status_code=400, detail="排班编号已存在")
    
    existing_slot = await Schedule.find_one(
        Schedule.employee_id == schedule.employee_id,
        Schedule.schedule_date == schedule.schedule_date,
        Schedule.time_slot == schedule.time_slot
    )
    if existing_slot:
        raise HTTPException(status_code=400, detail="同一员工同一时段不能重复排班")
    
    db_schedule = Schedule(**schedule.model_dump())
    await db_schedule.insert()
    return ScheduleResponse(
        id=str(db_schedule.id),
        schedule_id=db_schedule.schedule_id,
        employee_id=db_schedule.employee_id,
        employee_name=db_schedule.employee_name,
        schedule_date=db_schedule.schedule_date,
        time_slot=db_schedule.time_slot,
        created_at=db_schedule.created_at
    )


@router.get("", response_model=List[ScheduleResponse])
async def get_schedules(
    employee_id: Optional[str] = Query(None, description="员工编号"),
    employee_name: Optional[str] = Query(None, description="员工姓名"),
    schedule_date: Optional[str] = Query(None, description="排班日期"),
    current_user: User = Depends(get_current_user)
):
    query = {}
    if employee_id:
        query["employee_id"] = employee_id
    if employee_name:
        query["employee_name"] = {"$regex": employee_name, "$options": "i"}
    if schedule_date:
        query["schedule_date"] = schedule_date
    
    schedules = await Schedule.find(query).sort("-schedule_date", "-time_slot").to_list()
    return [
        ScheduleResponse(
            id=str(s.id),
            schedule_id=s.schedule_id,
            employee_id=s.employee_id,
            employee_name=s.employee_name,
            schedule_date=s.schedule_date,
            time_slot=s.time_slot,
            created_at=s.created_at
        ) for s in schedules
    ]


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(schedule_id: str, current_user: User = Depends(get_current_user)):
    schedule = await Schedule.find_one(Schedule.schedule_id == schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="排班不存在")
    return ScheduleResponse(
        id=str(schedule.id),
        schedule_id=schedule.schedule_id,
        employee_id=schedule.employee_id,
        employee_name=schedule.employee_name,
        schedule_date=schedule.schedule_date,
        time_slot=schedule.time_slot,
        created_at=schedule.created_at
    )


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(schedule_id: str, schedule_update: ScheduleUpdate, current_user: User = Depends(get_current_user)):
    schedule = await Schedule.find_one(Schedule.schedule_id == schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="排班不存在")
    
    update_data = schedule_update.model_dump(exclude_unset=True)
    
    new_date = update_data.get("schedule_date", schedule.schedule_date)
    new_slot = update_data.get("time_slot", schedule.time_slot)
    
    if "schedule_date" in update_data or "time_slot" in update_data:
        existing_slot = await Schedule.find_one(
            Schedule.id != schedule.id,
            Schedule.employee_id == schedule.employee_id,
            Schedule.schedule_date == new_date,
            Schedule.time_slot == new_slot
        )
        if existing_slot:
            raise HTTPException(status_code=400, detail="同一员工同一时段不能重复排班")
    
    for key, value in update_data.items():
        setattr(schedule, key, value)
    
    await schedule.save()
    return ScheduleResponse(
        id=str(schedule.id),
        schedule_id=schedule.schedule_id,
        employee_id=schedule.employee_id,
        employee_name=schedule.employee_name,
        schedule_date=schedule.schedule_date,
        time_slot=schedule.time_slot,
        created_at=schedule.created_at
    )


@router.delete("/{schedule_id}")
async def delete_schedule(schedule_id: str, current_user: User = Depends(get_current_user)):
    schedule = await Schedule.find_one(Schedule.schedule_id == schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="排班不存在")
    await schedule.delete()
    return {"message": "删除成功"}

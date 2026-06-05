from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from app.models.appointment import Appointment, AppointmentCreate, AppointmentUpdate, AppointmentResponse
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter()


def is_appointment_time_valid(appointment_date: str, time_slot: str) -> bool:
    try:
        now = datetime.now()
        appointment_str = f"{appointment_date} {time_slot.split('-')[0]}"
        appointment_dt = datetime.strptime(appointment_str, "%Y-%m-%d %H:%M")
        return appointment_dt >= now
    except:
        return True


@router.post("", response_model=AppointmentResponse)
async def create_appointment(appointment: AppointmentCreate, current_user: User = Depends(get_current_user)):
    existing = await Appointment.find_one(Appointment.appointment_no == appointment.appointment_no)
    if existing:
        raise HTTPException(status_code=400, detail="预约编号已存在")
    
    if not is_appointment_time_valid(appointment.appointment_date, appointment.time_slot):
        raise HTTPException(status_code=400, detail="预约时间不能早于当前日期时间")
    
    db_appointment = Appointment(**appointment.model_dump())
    await db_appointment.insert()
    return AppointmentResponse(
        id=str(db_appointment.id),
        appointment_no=db_appointment.appointment_no,
        customer_name=db_appointment.customer_name,
        phone=db_appointment.phone,
        service_id=db_appointment.service_id,
        service_name=db_appointment.service_name,
        employee_id=db_appointment.employee_id,
        employee_name=db_appointment.employee_name,
        appointment_date=db_appointment.appointment_date,
        time_slot=db_appointment.time_slot,
        status=db_appointment.status,
        created_at=db_appointment.created_at
    )


@router.get("", response_model=List[AppointmentResponse])
async def get_appointments(
    customer_name: Optional[str] = Query(None, description="客户姓名"),
    phone: Optional[str] = Query(None, description="联系电话"),
    service_id: Optional[str] = Query(None, description="服务项目编号"),
    appointment_date: Optional[str] = Query(None, description="预约日期"),
    status: Optional[str] = Query(None, description="预约状态"),
    current_user: User = Depends(get_current_user)
):
    query = {}
    if customer_name:
        query["customer_name"] = {"$regex": customer_name, "$options": "i"}
    if phone:
        query["phone"] = {"$regex": phone}
    if service_id:
        query["service_id"] = service_id
    if appointment_date:
        query["appointment_date"] = appointment_date
    if status:
        query["status"] = status
    
    appointments = await Appointment.find(query).sort("-created_at").to_list()
    return [
        AppointmentResponse(
            id=str(a.id),
            appointment_no=a.appointment_no,
            customer_name=a.customer_name,
            phone=a.phone,
            service_id=a.service_id,
            service_name=a.service_name,
            employee_id=a.employee_id,
            employee_name=a.employee_name,
            appointment_date=a.appointment_date,
            time_slot=a.time_slot,
            status=a.status,
            created_at=a.created_at
        ) for a in appointments
    ]


@router.get("/{appointment_no}", response_model=AppointmentResponse)
async def get_appointment(appointment_no: str, current_user: User = Depends(get_current_user)):
    appointment = await Appointment.find_one(Appointment.appointment_no == appointment_no)
    if not appointment:
        raise HTTPException(status_code=404, detail="预约不存在")
    return AppointmentResponse(
        id=str(appointment.id),
        appointment_no=appointment.appointment_no,
        customer_name=appointment.customer_name,
        phone=appointment.phone,
        service_id=appointment.service_id,
        service_name=appointment.service_name,
        employee_id=appointment.employee_id,
        employee_name=appointment.employee_name,
        appointment_date=appointment.appointment_date,
        time_slot=appointment.time_slot,
        status=appointment.status,
        created_at=appointment.created_at
    )


@router.put("/{appointment_no}", response_model=AppointmentResponse)
async def update_appointment(appointment_no: str, appointment_update: AppointmentUpdate, current_user: User = Depends(get_current_user)):
    appointment = await Appointment.find_one(Appointment.appointment_no == appointment_no)
    if not appointment:
        raise HTTPException(status_code=404, detail="预约不存在")
    
    if appointment_update.status and appointment.status == "已取消":
        raise HTTPException(status_code=400, detail="已取消的预约不能修改状态")
    
    update_data = appointment_update.model_dump(exclude_unset=True)
    
    if "appointment_date" in update_data or "time_slot" in update_data:
        new_date = update_data.get("appointment_date", appointment.appointment_date)
        new_slot = update_data.get("time_slot", appointment.time_slot)
        if not is_appointment_time_valid(new_date, new_slot):
            raise HTTPException(status_code=400, detail="预约时间不能早于当前日期时间")
    
    for key, value in update_data.items():
        setattr(appointment, key, value)
    
    await appointment.save()
    return AppointmentResponse(
        id=str(appointment.id),
        appointment_no=appointment.appointment_no,
        customer_name=appointment.customer_name,
        phone=appointment.phone,
        service_id=appointment.service_id,
        service_name=appointment.service_name,
        employee_id=appointment.employee_id,
        employee_name=appointment.employee_name,
        appointment_date=appointment.appointment_date,
        time_slot=appointment.time_slot,
        status=appointment.status,
        created_at=appointment.created_at
    )


@router.delete("/{appointment_no}")
async def delete_appointment(appointment_no: str, current_user: User = Depends(get_current_user)):
    appointment = await Appointment.find_one(Appointment.appointment_no == appointment_no)
    if not appointment:
        raise HTTPException(status_code=404, detail="预约不存在")
    await appointment.delete()
    return {"message": "删除成功"}


@router.post("/{appointment_no}/complete")
async def complete_appointment(appointment_no: str, current_user: User = Depends(get_current_user)):
    appointment = await Appointment.find_one(Appointment.appointment_no == appointment_no)
    if not appointment:
        raise HTTPException(status_code=404, detail="预约不存在")
    if appointment.status == "已取消":
        raise HTTPException(status_code=400, detail="已取消的预约不能办理服务")
    appointment.status = "已完成"
    await appointment.save()
    return {"message": "服务已完成"}


@router.post("/{appointment_no}/cancel")
async def cancel_appointment(appointment_no: str, current_user: User = Depends(get_current_user)):
    appointment = await Appointment.find_one(Appointment.appointment_no == appointment_no)
    if not appointment:
        raise HTTPException(status_code=404, detail="预约不存在")
    appointment.status = "已取消"
    await appointment.save()
    return {"message": "预约已取消"}

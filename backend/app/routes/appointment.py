from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from app.models.appointment import Appointment, AppointmentCreate, AppointmentUpdate, AppointmentResponse, AppointmentCompleteRequest
from app.models.user import User
from app.utils.auth import get_current_user
from app.utils.log import add_operation_log
from app.services import AppointmentService, BusinessException

router = APIRouter()


def _to_response(appointment: Appointment) -> AppointmentResponse:
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
        pay_method=appointment.pay_method,
        member_no=appointment.member_no,
        pay_amount=appointment.pay_amount,
        discount_rate=appointment.discount_rate,
        created_at=appointment.created_at,
    )


@router.post("", response_model=AppointmentResponse)
async def create_appointment(appointment: AppointmentCreate, current_user: User = Depends(get_current_user)):
    existing = await Appointment.find_one(Appointment.appointment_no == appointment.appointment_no)
    if existing:
        raise HTTPException(status_code=400, detail="预约编号已存在")

    if not AppointmentService.is_time_valid(appointment.appointment_date, appointment.time_slot):
        raise HTTPException(status_code=400, detail="预约时间不能早于当前日期时间")

    db_appointment = Appointment(**appointment.model_dump())
    await db_appointment.insert()

    await add_operation_log(
        operator=current_user.username,
        module="预约服务",
        action="新增预约",
        target_id=db_appointment.appointment_no,
        detail=f"新增预约：{db_appointment.customer_name} - {db_appointment.service_name}"
    )

    return _to_response(db_appointment)


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
    return [_to_response(a) for a in appointments]


@router.get("/{appointment_no}", response_model=AppointmentResponse)
async def get_appointment(appointment_no: str, current_user: User = Depends(get_current_user)):
    appointment = await Appointment.find_one(Appointment.appointment_no == appointment_no)
    if not appointment:
        raise HTTPException(status_code=404, detail="预约不存在")
    return _to_response(appointment)


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
        if not AppointmentService.is_time_valid(new_date, new_slot):
            raise HTTPException(status_code=400, detail="预约时间不能早于当前日期时间")

    for key, value in update_data.items():
        setattr(appointment, key, value)

    await appointment.save()

    await add_operation_log(
        operator=current_user.username,
        module="预约服务",
        action="修改预约",
        target_id=appointment.appointment_no,
        detail=f"修改预约：{appointment.customer_name} - {appointment.service_name}"
    )

    return _to_response(appointment)


@router.delete("/{appointment_no}")
async def delete_appointment(appointment_no: str, current_user: User = Depends(get_current_user)):
    appointment = await Appointment.find_one(Appointment.appointment_no == appointment_no)
    if not appointment:
        raise HTTPException(status_code=404, detail="预约不存在")
    await appointment.delete()

    await add_operation_log(
        operator=current_user.username,
        module="预约服务",
        action="删除预约",
        target_id=appointment_no,
        detail=f"删除预约：{appointment.customer_name} - {appointment.service_name}"
    )

    return {"message": "删除成功"}


@router.get("/{appointment_no}/stock-check")
async def check_appointment_stock(appointment_no: str, current_user: User = Depends(get_current_user)):
    try:
        result = await AppointmentService.check_stock(appointment_no)
    except BusinessException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    return {
        "has_template": result.has_template,
        "items": [
            {
                "consumable_no": item.consumable_no,
                "consumable_name": item.consumable_name,
                "required": item.required,
                "stock": item.stock,
                "unit": item.unit,
                "sufficient": item.sufficient,
                **({"reason": item.reason} if item.reason else {}),
            }
            for item in result.items
        ],
        "sufficient": result.sufficient,
        "insufficient_items": [
            {
                "consumable_no": item.consumable_no,
                "consumable_name": item.consumable_name,
                "required": item.required,
                "stock": item.stock,
                "unit": item.unit,
                "reason": item.reason or "",
            }
            for item in result.insufficient_items
        ],
    }


@router.post("/{appointment_no}/complete")
async def complete_appointment(
    appointment_no: str,
    request_data: AppointmentCompleteRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        result = await AppointmentService.complete_appointment(
            appointment_no=appointment_no,
            request_data=request_data,
            operator=current_user.username,
        )
    except BusinessException as e:
        detail = e.detail if e.detail else e.message
        raise HTTPException(status_code=e.status_code, detail=detail)

    return {
        "message": result.message,
        "pay_info": result.pay_info,
    }


@router.post("/{appointment_no}/cancel")
async def cancel_appointment(appointment_no: str, current_user: User = Depends(get_current_user)):
    try:
        result = await AppointmentService.cancel_appointment(
            appointment_no=appointment_no,
            operator=current_user.username,
        )
    except BusinessException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    return {"message": result.message}

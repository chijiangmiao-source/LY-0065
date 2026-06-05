from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from app.models.appointment import Appointment, AppointmentCreate, AppointmentUpdate, AppointmentResponse, AppointmentCompleteRequest
from app.models.service_consumable_template import ServiceConsumableTemplate
from app.models.consumable import Consumable
from app.models.usage import Usage
from app.models.service import Service
from app.models.member import Member
from app.models.member_level import MemberLevel
from app.models.member_consumption import MemberConsumption
from app.models.member_package import MemberPackage
from app.models.package_redemption import PackageRedemption
from app.models.user import User
from app.utils.auth import get_current_user
from app.utils.log import add_operation_log

router = APIRouter()


async def generate_redemption_no() -> str:
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"R{today}"
    last = await PackageRedemption.find(PackageRedemption.redemption_no.startswith(prefix)).sort("-redemption_no").first_or_none()
    if last:
        seq = int(last.redemption_no[-4:]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


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
        pay_method=db_appointment.pay_method,
        member_no=db_appointment.member_no,
        pay_amount=db_appointment.pay_amount,
        discount_rate=db_appointment.discount_rate,
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
            pay_method=a.pay_method,
            member_no=a.member_no,
            pay_amount=a.pay_amount,
            discount_rate=a.discount_rate,
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
        pay_method=appointment.pay_method,
        member_no=appointment.member_no,
        pay_amount=appointment.pay_amount,
        discount_rate=appointment.discount_rate,
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
        pay_method=appointment.pay_method,
        member_no=appointment.member_no,
        pay_amount=appointment.pay_amount,
        discount_rate=appointment.discount_rate,
        created_at=appointment.created_at
    )


@router.delete("/{appointment_no}")
async def delete_appointment(appointment_no: str, current_user: User = Depends(get_current_user)):
    appointment = await Appointment.find_one(Appointment.appointment_no == appointment_no)
    if not appointment:
        raise HTTPException(status_code=404, detail="预约不存在")
    await appointment.delete()
    return {"message": "删除成功"}


async def generate_usage_no() -> str:
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"LY{today}"
    last_usage = await Usage.find(Usage.usage_no.startswith(prefix)).sort("-usage_no").first_or_none()
    if last_usage:
        seq = int(last_usage.usage_no[-4:]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


@router.get("/{appointment_no}/stock-check")
async def check_appointment_stock(appointment_no: str, current_user: User = Depends(get_current_user)):
    appointment = await Appointment.find_one(Appointment.appointment_no == appointment_no)
    if not appointment:
        raise HTTPException(status_code=404, detail="预约不存在")

    template = await ServiceConsumableTemplate.find_one(
        ServiceConsumableTemplate.service_id == appointment.service_id,
        ServiceConsumableTemplate.status == "启用"
    )
    if not template or not template.items:
        return {
            "has_template": False,
            "items": [],
            "sufficient": True,
            "insufficient_items": []
        }

    items_detail = []
    insufficient_items = []
    for item in template.items:
        consumable = await Consumable.find_one(Consumable.consumable_no == item["consumable_no"])
        if not consumable:
            insufficient_items.append({
                "consumable_no": item["consumable_no"],
                "consumable_name": item["consumable_name"],
                "required": item["quantity"],
                "stock": 0,
                "unit": item.get("unit", "个"),
                "reason": "耗材不存在"
            })
            continue
        items_detail.append({
            "consumable_no": item["consumable_no"],
            "consumable_name": item["consumable_name"],
            "required": item["quantity"],
            "stock": consumable.stock_quantity,
            "unit": item.get("unit", "个"),
            "sufficient": consumable.stock_quantity >= item["quantity"]
        })
        if consumable.stock_quantity < item["quantity"]:
            insufficient_items.append({
                "consumable_no": item["consumable_no"],
                "consumable_name": item["consumable_name"],
                "required": item["quantity"],
                "stock": consumable.stock_quantity,
                "unit": item.get("unit", "个"),
                "reason": f"库存不足，需要 {item['quantity']} {item.get('unit', '个')}，当前仅有 {consumable.stock_quantity} {item.get('unit', '个')}"
            })

    return {
        "has_template": True,
        "items": items_detail,
        "sufficient": len(insufficient_items) == 0,
        "insufficient_items": insufficient_items
    }


async def generate_consumption_no() -> str:
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"C{today}"
    last = await MemberConsumption.find(MemberConsumption.consumption_no.startswith(prefix)).sort("-consumption_no").first_or_none()
    if last:
        seq = int(last.consumption_no[-4:]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


@router.post("/{appointment_no}/complete")
async def complete_appointment(
    appointment_no: str,
    request_data: AppointmentCompleteRequest,
    current_user: User = Depends(get_current_user)
):
    appointment = await Appointment.find_one(Appointment.appointment_no == appointment_no)
    if not appointment:
        raise HTTPException(status_code=404, detail="预约不存在")
    if appointment.status == "已取消":
        raise HTTPException(status_code=400, detail="已取消的预约不能办理服务")
    if appointment.status == "已完成":
        raise HTTPException(status_code=400, detail="该预约已完成")

    if request_data.pay_method not in ["余额", "现金", "次卡"]:
        raise HTTPException(status_code=400, detail="支付方式必须为'余额'、'现金'或'次卡'")

    service = await Service.find_one(Service.service_id == appointment.service_id)
    if not service:
        raise HTTPException(status_code=400, detail="服务项目不存在")

    original_price = service.price
    discount_rate = 1.0
    member = None
    balance_before = None
    balance_after = None
    member_package = None
    redemption_info = None
    mixed_pay_amount = None

    if request_data.pay_method == "次卡":
        if not request_data.member_no:
            raise HTTPException(status_code=400, detail="次卡核销必须选择会员")
        if not request_data.member_package_no:
            raise HTTPException(status_code=400, detail="次卡核销必须选择会员套餐")

        member = await Member.find_one(Member.member_no == request_data.member_no)
        if not member:
            raise HTTPException(status_code=404, detail="会员不存在")
        if member.phone != appointment.phone:
            raise HTTPException(status_code=400, detail="会员手机号与预约手机号不一致")
        if member.status != "正常":
            raise HTTPException(status_code=400, detail="该会员状态异常，无法使用次卡")

        member_package = await MemberPackage.find_one(
            MemberPackage.member_package_no == request_data.member_package_no
        )
        if not member_package:
            raise HTTPException(status_code=404, detail="会员套餐不存在")
        if member_package.member_no != request_data.member_no:
            raise HTTPException(status_code=400, detail="该套餐不属于所选会员")
        if member_package.status != "生效中":
            raise HTTPException(status_code=400, detail=f"套餐状态异常：{member_package.status}，无法核销")
        if member_package.expire_date < datetime.now():
            raise HTTPException(status_code=400, detail=f"套餐已于 {member_package.expire_date.strftime('%Y-%m-%d')} 过期，无法核销")
        if member_package.remaining_times < 1:
            raise HTTPException(status_code=400, detail="套餐剩余次数不足，无法核销")

        if member_package.applicable_service_ids:
            if appointment.service_id not in member_package.applicable_service_ids:
                raise HTTPException(
                    status_code=400,
                    detail=f"该套餐仅适用于：{', '.join(member_package.applicable_service_names)}，当前服务不匹配"
                )

        if member_package.applicable_employee_ids and appointment.employee_id:
            if appointment.employee_id not in member_package.applicable_employee_ids:
                raise HTTPException(
                    status_code=400,
                    detail="该套餐不支持当前服务员工"
                )

        remaining_before = member_package.remaining_times
        member_package.used_times += 1
        member_package.remaining_times -= 1
        remaining_after = member_package.remaining_times

        if request_data.use_mixed_payment and not member_package.allow_mixed_payment:
            raise HTTPException(status_code=400, detail="该套餐不支持与余额混合支付")

        actual_amount = 0.0
        mixed_payment = False

        if request_data.use_mixed_payment:
            level = await MemberLevel.find_one(MemberLevel.level_id == member.level_id)
            if level:
                discount_rate = level.discount_rate
            mixed_pay_amount = round(original_price * discount_rate, 2)
            if member.balance < mixed_pay_amount:
                raise HTTPException(
                    status_code=400,
                    detail=f"混合支付余额不足，当前余额：{member.balance} 元，需支付：{mixed_pay_amount} 元"
                )
            balance_before = member.balance
            balance_after = round(member.balance - mixed_pay_amount, 2)
            member.balance = balance_after
            member.total_consumption += mixed_pay_amount
            actual_amount = mixed_pay_amount
            mixed_payment = True

        await member_package.save()

        redemption = PackageRedemption(
            redemption_no=await generate_redemption_no(),
            member_package_no=member_package.member_package_no,
            member_no=member.member_no,
            member_name=member.name,
            phone=member.phone,
            package_no=member_package.package_no,
            package_name=member_package.package_name,
            appointment_no=appointment.appointment_no,
            service_id=appointment.service_id,
            service_name=appointment.service_name,
            employee_id=appointment.employee_id,
            employee_name=appointment.employee_name,
            redeem_times=1,
            remaining_before=remaining_before,
            remaining_after=remaining_after,
            mixed_payment=mixed_payment,
            mixed_pay_amount=mixed_pay_amount,
            operator=current_user.username,
            remark=f"预约服务完成次卡核销"
        )
        await redemption.insert()

        redemption_info = {
            "member_package_no": member_package.member_package_no,
            "package_name": member_package.package_name,
            "remaining_before": remaining_before,
            "remaining_after": remaining_after,
            "mixed_payment": mixed_payment,
            "mixed_pay_amount": mixed_pay_amount
        }

        await member.save()

    elif request_data.pay_method == "余额":
        if not request_data.member_no:
            raise HTTPException(status_code=400, detail="余额支付必须选择会员")
        member = await Member.find_one(Member.member_no == request_data.member_no)
        if not member:
            raise HTTPException(status_code=404, detail="会员不存在")
        if member.phone != appointment.phone:
            raise HTTPException(status_code=400, detail="会员手机号与预约手机号不一致")
        if member.status != "正常":
            raise HTTPException(status_code=400, detail="该会员状态异常，无法使用余额支付")
        level = await MemberLevel.find_one(MemberLevel.level_id == member.level_id)
        if level:
            discount_rate = level.discount_rate
        actual_amount = round(original_price * discount_rate, 2)
        if member.balance < actual_amount:
            raise HTTPException(
                status_code=400,
                detail=f"会员余额不足，当前余额：{member.balance} 元，需支付：{actual_amount} 元"
            )
        balance_before = member.balance
        balance_after = round(member.balance - actual_amount, 2)
        member.balance = balance_after
        member.total_consumption += actual_amount
        await member.save()
    else:
        actual_amount = original_price

    template = await ServiceConsumableTemplate.find_one(
        ServiceConsumableTemplate.service_id == appointment.service_id,
        ServiceConsumableTemplate.status == "启用"
    )

    if template and template.items:
        insufficient_items = []
        consumables_to_update = []
        for item in template.items:
            consumable = await Consumable.find_one(Consumable.consumable_no == item["consumable_no"])
            if not consumable:
                insufficient_items.append(f"{item['consumable_name']}: 耗材不存在")
                continue
            if consumable.stock_quantity < item["quantity"]:
                insufficient_items.append(
                    f"{item['consumable_name']}: 需要 {item['quantity']} {item.get('unit', '个')}，"
                    f"当前库存仅有 {consumable.stock_quantity} {item.get('unit', '个')}"
                )
                continue
            consumables_to_update.append((consumable, item))

        if insufficient_items:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "库存不足，无法完成服务，请先补充耗材库存",
                    "insufficient_items": insufficient_items
                }
            )

        for consumable, item in consumables_to_update:
            consumable.stock_quantity -= item["quantity"]
            await consumable.save()

            usage_no = await generate_usage_no()
            db_usage = Usage(
                usage_no=usage_no,
                consumable_no=item["consumable_no"],
                consumable_name=item["consumable_name"],
                quantity=item["quantity"],
                employee_id=appointment.employee_id or current_user.username,
                employee_name=appointment.employee_name or current_user.username,
                usage_date=datetime.now().strftime("%Y-%m-%d"),
                source_type="自动扣减",
                appointment_no=appointment.appointment_no,
                remark=f"服务完成自动扣减: {appointment.service_name}"
            )
            await db_usage.insert()

    consumption = MemberConsumption(
        consumption_no=await generate_consumption_no(),
        member_no=request_data.member_no,
        member_name=member.name if member else None,
        phone=member.phone if member else appointment.phone,
        appointment_no=appointment.appointment_no,
        service_id=appointment.service_id,
        service_name=appointment.service_name,
        original_price=original_price,
        discount_rate=discount_rate,
        actual_amount=actual_amount,
        pay_method=request_data.pay_method,
        balance_before=balance_before,
        balance_after=balance_after,
        operator=current_user.username,
        remark=f"预约服务完成支付{'（次卡核销）' if request_data.pay_method == '次卡' else ''}"
    )
    await consumption.insert()

    appointment.status = "已完成"
    appointment.pay_method = request_data.pay_method
    appointment.member_no = request_data.member_no
    appointment.pay_amount = actual_amount
    appointment.discount_rate = discount_rate
    await appointment.save()

    if request_data.pay_method == "次卡":
        pay_detail = f"次卡核销（{member_package.package_name}），剩余次数：{remaining_after}次"
        if mixed_payment and mixed_pay_amount:
            pay_detail += f"，混合余额支付 {mixed_pay_amount} 元"
    else:
        pay_detail = f"{request_data.pay_method}支付 {actual_amount} 元"
        if discount_rate < 1.0:
            pay_detail += f"（原价 {original_price} 元，折扣 {(discount_rate * 10):.1f} 折）"

    await add_operation_log(
        operator=current_user.username,
        module="预约服务",
        action="完成服务",
        target_id=appointment.appointment_no,
        detail=f"完成预约服务 {appointment.customer_name} - {appointment.service_name}，{pay_detail}"
    )

    return {
        "message": f"服务已完成，耗材已自动扣减，{pay_detail}",
        "pay_info": {
            "pay_method": request_data.pay_method,
            "original_price": original_price,
            "discount_rate": discount_rate,
            "actual_amount": actual_amount,
            "balance_before": balance_before,
            "balance_after": balance_after,
            "redemption": redemption_info
        }
    }


@router.post("/{appointment_no}/cancel")
async def cancel_appointment(appointment_no: str, current_user: User = Depends(get_current_user)):
    appointment = await Appointment.find_one(Appointment.appointment_no == appointment_no)
    if not appointment:
        raise HTTPException(status_code=404, detail="预约不存在")
    if appointment.status == "已取消":
        raise HTTPException(status_code=400, detail="预约已取消")

    if appointment.status == "已完成":
        auto_usages = await Usage.find(
            Usage.appointment_no == appointment_no,
            Usage.source_type == "自动扣减"
        ).to_list()
        for usage in auto_usages:
            consumable = await Consumable.find_one(Consumable.consumable_no == usage.consumable_no)
            if consumable:
                consumable.stock_quantity += usage.quantity
                await consumable.save()
            await usage.delete()

        if appointment.pay_method == "次卡":
            redemption = await PackageRedemption.find_one(
                PackageRedemption.appointment_no == appointment_no
            )
            if redemption:
                member_package = await MemberPackage.find_one(
                    MemberPackage.member_package_no == redemption.member_package_no
                )
                if member_package and member_package.status == "生效中":
                    member_package.used_times = max(0, member_package.used_times - redemption.redeem_times)
                    member_package.remaining_times += redemption.redeem_times
                    await member_package.save()

                    if redemption.mixed_payment and redemption.mixed_pay_amount and appointment.member_no:
                        member = await Member.find_one(Member.member_no == appointment.member_no)
                        if member:
                            member.balance = round(member.balance + redemption.mixed_pay_amount, 2)
                            member.total_consumption = max(0, member.total_consumption - redemption.mixed_pay_amount)
                            await member.save()

                await redemption.delete()

        if appointment.pay_method == "余额" and appointment.member_no and appointment.pay_amount:
            member = await Member.find_one(Member.member_no == appointment.member_no)
            if member:
                member.balance = round(member.balance + appointment.pay_amount, 2)
                member.total_consumption = max(0, member.total_consumption - appointment.pay_amount)
                await member.save()

            consumption = await MemberConsumption.find_one(
                MemberConsumption.appointment_no == appointment_no
            )
            if consumption:
                await consumption.delete()

        if appointment.pay_method == "次卡" and appointment.member_no:
            consumption = await MemberConsumption.find_one(
                MemberConsumption.appointment_no == appointment_no
            )
            if consumption:
                await consumption.delete()

    appointment.status = "已取消"
    await appointment.save()

    await add_operation_log(
        operator=current_user.username,
        module="预约服务",
        action="取消预约",
        target_id=appointment.appointment_no,
        detail=f"取消预约 {appointment.customer_name} - {appointment.service_name}"
    )

    return {"message": "预约已取消，库存已退还"}

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from app.models.member_level import MemberLevel, MemberLevelCreate, MemberLevelUpdate, MemberLevelResponse
from app.models.member import Member, MemberCreate, MemberUpdate, MemberResponse
from app.models.member_recharge import MemberRecharge, MemberRechargeCreate, MemberRechargeResponse
from app.models.member_consumption import MemberConsumption, MemberConsumptionCreate, MemberConsumptionResponse
from app.models.operation_log import OperationLog, OperationLogResponse
from app.models.user import User
from app.utils.auth import get_current_user
from app.utils.log import add_operation_log

router = APIRouter()


# ==================== 会员等级管理 ====================

async def generate_level_id() -> str:
    last = await MemberLevel.find_all().sort("-level_id").first_or_none()
    if last:
        seq = int(last.level_id[2:]) + 1
    else:
        seq = 1
    return f"LV{seq:03d}"


@router.post("/levels", response_model=MemberLevelResponse)
async def create_member_level(level: MemberLevelCreate, current_user: User = Depends(get_current_user)):
    existing = await MemberLevel.find_one(MemberLevel.level_id == level.level_id)
    if existing:
        raise HTTPException(status_code=400, detail="等级编号已存在")
    existing_name = await MemberLevel.find_one(MemberLevel.name == level.name)
    if existing_name:
        raise HTTPException(status_code=400, detail="等级名称已存在")
    if not level.level_id:
        level.level_id = await generate_level_id()
    db_level = MemberLevel(**level.model_dump())
    await db_level.insert()
    await add_operation_log(
        operator=current_user.username,
        module="会员等级",
        action="新增",
        target_id=db_level.level_id,
        detail=f"新增会员等级：{db_level.name}，折扣率：{db_level.discount_rate}"
    )
    return MemberLevelResponse(
        id=str(db_level.id),
        level_id=db_level.level_id,
        name=db_level.name,
        min_recharge=db_level.min_recharge,
        discount_rate=db_level.discount_rate,
        description=db_level.description,
        status=db_level.status,
        created_at=db_level.created_at
    )


@router.get("/levels", response_model=List[MemberLevelResponse])
async def get_member_levels(
    status: Optional[str] = Query(None, description="状态"),
    current_user: User = Depends(get_current_user)
):
    query = {}
    if status:
        query["status"] = status
    levels = await MemberLevel.find(query).sort("-created_at").to_list()
    return [
        MemberLevelResponse(
            id=str(l.id),
            level_id=l.level_id,
            name=l.name,
            min_recharge=l.min_recharge,
            discount_rate=l.discount_rate,
            description=l.description,
            status=l.status,
            created_at=l.created_at
        ) for l in levels
    ]


@router.get("/levels/{level_id}", response_model=MemberLevelResponse)
async def get_member_level(level_id: str, current_user: User = Depends(get_current_user)):
    level = await MemberLevel.find_one(MemberLevel.level_id == level_id)
    if not level:
        raise HTTPException(status_code=404, detail="会员等级不存在")
    return MemberLevelResponse(
        id=str(level.id),
        level_id=level.level_id,
        name=level.name,
        min_recharge=level.min_recharge,
        discount_rate=level.discount_rate,
        description=level.description,
        status=level.status,
        created_at=level.created_at
    )


@router.put("/levels/{level_id}", response_model=MemberLevelResponse)
async def update_member_level(level_id: str, level_update: MemberLevelUpdate, current_user: User = Depends(get_current_user)):
    level = await MemberLevel.find_one(MemberLevel.level_id == level_id)
    if not level:
        raise HTTPException(status_code=404, detail="会员等级不存在")
    update_data = level_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(level, key, value)
    await level.save()
    await add_operation_log(
        operator=current_user.username,
        module="会员等级",
        action="修改",
        target_id=level.level_id,
        detail=f"修改会员等级：{level.name}"
    )
    return MemberLevelResponse(
        id=str(level.id),
        level_id=level.level_id,
        name=level.name,
        min_recharge=level.min_recharge,
        discount_rate=level.discount_rate,
        description=level.description,
        status=level.status,
        created_at=level.created_at
    )


@router.delete("/levels/{level_id}")
async def delete_member_level(level_id: str, current_user: User = Depends(get_current_user)):
    level = await MemberLevel.find_one(MemberLevel.level_id == level_id)
    if not level:
        raise HTTPException(status_code=404, detail="会员等级不存在")
    members = await Member.find(Member.level_id == level_id).count()
    if members > 0:
        raise HTTPException(status_code=400, detail=f"该等级下还有 {members} 名会员，无法删除")
    await level.delete()
    await add_operation_log(
        operator=current_user.username,
        module="会员等级",
        action="删除",
        target_id=level_id,
        detail=f"删除会员等级：{level.name}"
    )
    return {"message": "删除成功"}


# ==================== 会员档案管理 ====================

async def generate_member_no() -> str:
    today = datetime.now().strftime("%Y%m")
    prefix = f"M{today}"
    last = await Member.find(Member.member_no.startswith(prefix)).sort("-member_no").first_or_none()
    if last:
        seq = int(last.member_no[-4:]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


@router.post("", response_model=MemberResponse)
async def create_member(member: MemberCreate, current_user: User = Depends(get_current_user)):
    if member.member_no:
        existing = await Member.find_one(Member.member_no == member.member_no)
        if existing:
            raise HTTPException(status_code=400, detail="会员编号已存在")
    else:
        member.member_no = await generate_member_no()
    existing_phone = await Member.find_one(Member.phone == member.phone)
    if existing_phone:
        raise HTTPException(status_code=400, detail="该手机号已注册会员")
    level = await MemberLevel.find_one(MemberLevel.level_id == member.level_id)
    if not level:
        raise HTTPException(status_code=400, detail="会员等级不存在")
    db_member = Member(**member.model_dump())
    await db_member.insert()
    await add_operation_log(
        operator=current_user.username,
        module="会员档案",
        action="新增",
        target_id=db_member.member_no,
        detail=f"新增会员：{db_member.name}，等级：{db_member.level_name}"
    )
    return MemberResponse(
        id=str(db_member.id),
        member_no=db_member.member_no,
        name=db_member.name,
        phone=db_member.phone,
        gender=db_member.gender,
        level_id=db_member.level_id,
        level_name=db_member.level_name,
        balance=db_member.balance,
        total_recharge=db_member.total_recharge,
        total_consumption=db_member.total_consumption,
        remark=db_member.remark,
        status=db_member.status,
        created_at=db_member.created_at
    )


@router.get("", response_model=List[MemberResponse])
async def get_members(
    member_no: Optional[str] = Query(None, description="会员编号"),
    name: Optional[str] = Query(None, description="会员姓名"),
    phone: Optional[str] = Query(None, description="联系电话"),
    level_id: Optional[str] = Query(None, description="会员等级"),
    status: Optional[str] = Query(None, description="状态"),
    current_user: User = Depends(get_current_user)
):
    query = {}
    if member_no:
        query["member_no"] = {"$regex": member_no}
    if name:
        query["name"] = {"$regex": name, "$options": "i"}
    if phone:
        query["phone"] = {"$regex": phone}
    if level_id:
        query["level_id"] = level_id
    if status:
        query["status"] = status
    members = await Member.find(query).sort("-created_at").to_list()
    return [
        MemberResponse(
            id=str(m.id),
            member_no=m.member_no,
            name=m.name,
            phone=m.phone,
            gender=m.gender,
            level_id=m.level_id,
            level_name=m.level_name,
            balance=m.balance,
            total_recharge=m.total_recharge,
            total_consumption=m.total_consumption,
            remark=m.remark,
            status=m.status,
            created_at=m.created_at
        ) for m in members
    ]


@router.get("/{member_no}", response_model=MemberResponse)
async def get_member(member_no: str, current_user: User = Depends(get_current_user)):
    member = await Member.find_one(Member.member_no == member_no)
    if not member:
        raise HTTPException(status_code=404, detail="会员不存在")
    return MemberResponse(
        id=str(member.id),
        member_no=member.member_no,
        name=member.name,
        phone=member.phone,
        gender=member.gender,
        level_id=member.level_id,
        level_name=member.level_name,
        balance=member.balance,
        total_recharge=member.total_recharge,
        total_consumption=member.total_consumption,
        remark=member.remark,
        status=member.status,
        created_at=member.created_at
    )


@router.get("/phone/{phone}", response_model=MemberResponse)
async def get_member_by_phone(phone: str, current_user: User = Depends(get_current_user)):
    member = await Member.find_one(Member.phone == phone)
    if not member:
        raise HTTPException(status_code=404, detail="未找到该手机号对应的会员")
    return MemberResponse(
        id=str(member.id),
        member_no=member.member_no,
        name=member.name,
        phone=member.phone,
        gender=member.gender,
        level_id=member.level_id,
        level_name=member.level_name,
        balance=member.balance,
        total_recharge=member.total_recharge,
        total_consumption=member.total_consumption,
        remark=member.remark,
        status=member.status,
        created_at=member.created_at
    )


@router.put("/{member_no}", response_model=MemberResponse)
async def update_member(member_no: str, member_update: MemberUpdate, current_user: User = Depends(get_current_user)):
    member = await Member.find_one(Member.member_no == member_no)
    if not member:
        raise HTTPException(status_code=404, detail="会员不存在")
    update_data = member_update.model_dump(exclude_unset=True)
    if "phone" in update_data and update_data["phone"] != member.phone:
        existing_phone = await Member.find_one(Member.phone == update_data["phone"])
        if existing_phone:
            raise HTTPException(status_code=400, detail="该手机号已被其他会员使用")
    if "level_id" in update_data:
        level = await MemberLevel.find_one(MemberLevel.level_id == update_data["level_id"])
        if not level:
            raise HTTPException(status_code=400, detail="会员等级不存在")
        if "level_name" not in update_data:
            update_data["level_name"] = level.name
    for key, value in update_data.items():
        setattr(member, key, value)
    await member.save()
    await add_operation_log(
        operator=current_user.username,
        module="会员档案",
        action="修改",
        target_id=member.member_no,
        detail=f"修改会员信息：{member.name}"
    )
    return MemberResponse(
        id=str(member.id),
        member_no=member.member_no,
        name=member.name,
        phone=member.phone,
        gender=member.gender,
        level_id=member.level_id,
        level_name=member.level_name,
        balance=member.balance,
        total_recharge=member.total_recharge,
        total_consumption=member.total_consumption,
        remark=member.remark,
        status=member.status,
        created_at=member.created_at
    )


@router.delete("/{member_no}")
async def delete_member(member_no: str, current_user: User = Depends(get_current_user)):
    member = await Member.find_one(Member.member_no == member_no)
    if not member:
        raise HTTPException(status_code=404, detail="会员不存在")
    if member.balance > 0:
        raise HTTPException(status_code=400, detail=f"该会员还有余额 {member.balance} 元，无法删除")
    await member.delete()
    await add_operation_log(
        operator=current_user.username,
        module="会员档案",
        action="删除",
        target_id=member_no,
        detail=f"删除会员：{member.name}"
    )
    return {"message": "删除成功"}


# ==================== 会员储值充值 ====================

async def generate_recharge_no() -> str:
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"R{today}"
    last = await MemberRecharge.find(MemberRecharge.recharge_no.startswith(prefix)).sort("-recharge_no").first_or_none()
    if last:
        seq = int(last.recharge_no[-4:]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


@router.post("/{member_no}/recharge", response_model=MemberRechargeResponse)
async def recharge_member(member_no: str, recharge: MemberRechargeCreate, current_user: User = Depends(get_current_user)):
    member = await Member.find_one(Member.member_no == member_no)
    if not member:
        raise HTTPException(status_code=404, detail="会员不存在")
    if member.status != "正常":
        raise HTTPException(status_code=400, detail="该会员状态异常，无法充值")
    if recharge.recharge_amount <= 0:
        raise HTTPException(status_code=400, detail="充值金额必须大于0")

    balance_before = member.balance
    total_amount = recharge.recharge_amount + (recharge.gift_amount or 0)
    balance_after = balance_before + total_amount

    db_recharge = MemberRecharge(
        recharge_no=await generate_recharge_no(),
        member_no=member.member_no,
        member_name=member.name,
        phone=member.phone,
        recharge_amount=recharge.recharge_amount,
        gift_amount=recharge.gift_amount or 0,
        total_amount=total_amount,
        balance_before=balance_before,
        balance_after=balance_after,
        operator=current_user.username,
        remark=recharge.remark,
    )
    await db_recharge.insert()

    member.balance = balance_after
    member.total_recharge += recharge.recharge_amount
    await member.save()

    level = await MemberLevel.find_one(MemberLevel.level_id == member.level_id)
    new_level = await MemberLevel.find(
        MemberLevel.min_recharge <= member.total_recharge,
        MemberLevel.status == "启用"
    ).sort("-min_recharge").first_or_none()
    if new_level and level and new_level.min_recharge > level.min_recharge:
        member.level_id = new_level.level_id
        member.level_name = new_level.name
        await member.save()
        await add_operation_log(
            operator=current_user.username,
            module="会员等级",
            action="自动升级",
            target_id=member.member_no,
            detail=f"会员 {member.name} 自动升级为：{new_level.name}"
        )

    await add_operation_log(
        operator=current_user.username,
        module="会员储值",
        action="充值",
        target_id=member.member_no,
        detail=f"为会员 {member.name} 充值：{recharge.recharge_amount} 元，赠送：{recharge.gift_amount or 0} 元"
    )

    return MemberRechargeResponse(
        id=str(db_recharge.id),
        recharge_no=db_recharge.recharge_no,
        member_no=db_recharge.member_no,
        member_name=db_recharge.member_name,
        phone=db_recharge.phone,
        recharge_amount=db_recharge.recharge_amount,
        gift_amount=db_recharge.gift_amount,
        total_amount=db_recharge.total_amount,
        balance_before=db_recharge.balance_before,
        balance_after=db_recharge.balance_after,
        operator=db_recharge.operator,
        remark=db_recharge.remark,
        created_at=db_recharge.created_at
    )


@router.get("/{member_no}/recharges", response_model=List[MemberRechargeResponse])
async def get_member_recharges(
    member_no: str,
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user)
):
    member = await Member.find_one(Member.member_no == member_no)
    if not member:
        raise HTTPException(status_code=404, detail="会员不存在")
    query: dict = {"member_no": member_no}
    if start_date:
        date_start = datetime.strptime(start_date, "%Y-%m-%d")
        query["created_at"] = {"$gte": date_start}
    if end_date:
        date_end = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        query.setdefault("created_at", {})
        query["created_at"]["$lte"] = date_end
    recharges = await MemberRecharge.find(query).sort("-created_at").to_list()
    return [
        MemberRechargeResponse(
            id=str(r.id),
            recharge_no=r.recharge_no,
            member_no=r.member_no,
            member_name=r.member_name,
            phone=r.phone,
            recharge_amount=r.recharge_amount,
            gift_amount=r.gift_amount,
            total_amount=r.total_amount,
            balance_before=r.balance_before,
            balance_after=r.balance_after,
            operator=r.operator,
            remark=r.remark,
            created_at=r.created_at
        ) for r in recharges
    ]


# ==================== 消费记录 ====================

async def generate_consumption_no() -> str:
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"C{today}"
    last = await MemberConsumption.find(MemberConsumption.consumption_no.startswith(prefix)).sort("-consumption_no").first_or_none()
    if last:
        seq = int(last.consumption_no[-4:]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


@router.get("/{member_no}/consumptions", response_model=List[MemberConsumptionResponse])
async def get_member_consumptions(
    member_no: str,
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user)
):
    member = await Member.find_one(Member.member_no == member_no)
    if not member:
        raise HTTPException(status_code=404, detail="会员不存在")
    query: dict = {"member_no": member_no}
    if start_date:
        date_start = datetime.strptime(start_date, "%Y-%m-%d")
        query["created_at"] = {"$gte": date_start}
    if end_date:
        date_end = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        query.setdefault("created_at", {})
        query["created_at"]["$lte"] = date_end
    consumptions = await MemberConsumption.find(query).sort("-created_at").to_list()
    return [
        MemberConsumptionResponse(
            id=str(c.id),
            consumption_no=c.consumption_no,
            member_no=c.member_no,
            member_name=c.member_name,
            phone=c.phone,
            appointment_no=c.appointment_no,
            service_id=c.service_id,
            service_name=c.service_name,
            original_price=c.original_price,
            discount_rate=c.discount_rate,
            actual_amount=c.actual_amount,
            pay_method=c.pay_method,
            balance_before=c.balance_before,
            balance_after=c.balance_after,
            operator=c.operator,
            remark=c.remark,
            created_at=c.created_at
        ) for c in consumptions
    ]


@router.get("/consumptions/all", response_model=List[MemberConsumptionResponse])
async def get_all_consumptions(
    member_no: Optional[str] = Query(None, description="会员编号"),
    pay_method: Optional[str] = Query(None, description="支付方式"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user)
):
    query: dict = {}
    if member_no:
        query["member_no"] = member_no
    if pay_method:
        query["pay_method"] = pay_method
    if start_date:
        date_start = datetime.strptime(start_date, "%Y-%m-%d")
        query["created_at"] = {"$gte": date_start}
    if end_date:
        date_end = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        query.setdefault("created_at", {})
        query["created_at"]["$lte"] = date_end
    consumptions = await MemberConsumption.find(query).sort("-created_at").to_list()
    return [
        MemberConsumptionResponse(
            id=str(c.id),
            consumption_no=c.consumption_no,
            member_no=c.member_no,
            member_name=c.member_name,
            phone=c.phone,
            appointment_no=c.appointment_no,
            service_id=c.service_id,
            service_name=c.service_name,
            original_price=c.original_price,
            discount_rate=c.discount_rate,
            actual_amount=c.actual_amount,
            pay_method=c.pay_method,
            balance_before=c.balance_before,
            balance_after=c.balance_after,
            operator=c.operator,
            remark=c.remark,
            created_at=c.created_at
        ) for c in consumptions
    ]


# ==================== 操作日志 ====================

@router.get("/logs/all", response_model=List[OperationLogResponse])
async def get_operation_logs(
    operator: Optional[str] = Query(None, description="操作人"),
    module: Optional[str] = Query(None, description="模块"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user)
):
    query: dict = {}
    if operator:
        query["operator"] = {"$regex": operator, "$options": "i"}
    if module:
        query["module"] = module
    if start_date:
        date_start = datetime.strptime(start_date, "%Y-%m-%d")
        query["created_at"] = {"$gte": date_start}
    if end_date:
        date_end = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        query.setdefault("created_at", {})
        query["created_at"]["$lte"] = date_end
    logs = await OperationLog.find(query).sort("-created_at").to_list(length=500)
    return [
        OperationLogResponse(
            id=str(l.id),
            log_id=l.log_id,
            operator=l.operator,
            module=l.module,
            action=l.action,
            target_id=l.target_id,
            detail=l.detail,
            created_at=l.created_at
        ) for l in logs
    ]

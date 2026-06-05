from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from app.models.package_card import PackageCard, PackageCardCreate, PackageCardUpdate, PackageCardResponse
from app.models.member_package import MemberPackage, MemberPackageCreate, MemberPackageRenew, MemberPackageStatusUpdate, MemberPackageResponse
from app.models.package_redemption import PackageRedemption, PackageRedemptionResponse
from app.models.member import Member
from app.models.service import Service
from app.models.user import User
from app.utils.auth import get_current_user
from app.utils.log import add_operation_log

router = APIRouter()


async def generate_package_no() -> str:
    today = datetime.now().strftime("%Y%m")
    prefix = f"P{today}"
    last = await PackageCard.find(PackageCard.package_no.startswith(prefix)).sort("-package_no").first_or_none()
    if last:
        seq = int(last.package_no[-4:]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


async def generate_member_package_no() -> str:
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"MP{today}"
    last = await MemberPackage.find(MemberPackage.member_package_no.startswith(prefix)).sort("-member_package_no").first_or_none()
    if last:
        seq = int(last.member_package_no[-4:]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


async def generate_redemption_no() -> str:
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"R{today}"
    last = await PackageRedemption.find(PackageRedemption.redemption_no.startswith(prefix)).sort("-redemption_no").first_or_none()
    if last:
        seq = int(last.redemption_no[-4:]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


async def check_and_update_package_expiry(member_package: MemberPackage) -> MemberPackage:
    if member_package.status == "生效中" and member_package.expire_date < datetime.now():
        member_package.status = "已过期"
        await member_package.save()
    return member_package


@router.post("", response_model=PackageCardResponse)
async def create_package_card(
    package: PackageCardCreate,
    current_user: User = Depends(get_current_user)
):
    if package.package_no:
        existing = await PackageCard.find_one(PackageCard.package_no == package.package_no)
        if existing:
            raise HTTPException(status_code=400, detail="套餐编号已存在")
    else:
        package.package_no = await generate_package_no()

    existing_name = await PackageCard.find_one(PackageCard.name == package.name)
    if existing_name:
        raise HTTPException(status_code=400, detail="套餐名称已存在")

    if package.applicable_service_ids:
        services = await Service.find(Service.service_id.in_(package.applicable_service_ids)).to_list()
        if len(services) != len(package.applicable_service_ids):
            raise HTTPException(status_code=400, detail="存在无效的服务项目编号")
        if not package.applicable_service_names:
            package.applicable_service_names = [s.name for s in services]

    db_package = PackageCard(**package.model_dump(exclude_unset=True))
    await db_package.insert()

    await add_operation_log(
        operator=current_user.username,
        module="套餐管理",
        action="新增套餐",
        target_id=db_package.package_no,
        detail=f"新增套餐：{db_package.name}，价格：{db_package.price}元，次数：{db_package.total_times + db_package.gift_times}次"
    )

    return PackageCardResponse(
        id=str(db_package.id),
        package_no=db_package.package_no,
        name=db_package.name,
        package_type=db_package.package_type,
        price=db_package.price,
        total_times=db_package.total_times,
        gift_times=db_package.gift_times,
        valid_days=db_package.valid_days,
        applicable_service_ids=db_package.applicable_service_ids,
        applicable_service_names=db_package.applicable_service_names,
        applicable_employee_ids=db_package.applicable_employee_ids,
        applicable_store_ids=db_package.applicable_store_ids,
        allow_mixed_payment=db_package.allow_mixed_payment,
        description=db_package.description,
        status=db_package.status,
        created_at=db_package.created_at
    )


@router.get("", response_model=List[PackageCardResponse])
async def get_package_cards(
    name: Optional[str] = Query(None, description="套餐名称"),
    package_type: Optional[str] = Query(None, description="套餐类型"),
    status: Optional[str] = Query(None, description="状态"),
    current_user: User = Depends(get_current_user)
):
    query = {}
    if name:
        query["name"] = {"$regex": name, "$options": "i"}
    if package_type:
        query["package_type"] = package_type
    if status:
        query["status"] = status

    packages = await PackageCard.find(query).sort("-created_at").to_list()
    return [
        PackageCardResponse(
            id=str(p.id),
            package_no=p.package_no,
            name=p.name,
            package_type=p.package_type,
            price=p.price,
            total_times=p.total_times,
            gift_times=p.gift_times,
            valid_days=p.valid_days,
            applicable_service_ids=p.applicable_service_ids,
            applicable_service_names=p.applicable_service_names,
            applicable_employee_ids=p.applicable_employee_ids,
            applicable_store_ids=p.applicable_store_ids,
            allow_mixed_payment=p.allow_mixed_payment,
            description=p.description,
            status=p.status,
            created_at=p.created_at
        ) for p in packages
    ]


@router.get("/{package_no}", response_model=PackageCardResponse)
async def get_package_card(package_no: str, current_user: User = Depends(get_current_user)):
    package = await PackageCard.find_one(PackageCard.package_no == package_no)
    if not package:
        raise HTTPException(status_code=404, detail="套餐不存在")
    return PackageCardResponse(
        id=str(package.id),
        package_no=package.package_no,
        name=package.name,
        package_type=package.package_type,
        price=package.price,
        total_times=package.total_times,
        gift_times=package.gift_times,
        valid_days=package.valid_days,
        applicable_service_ids=package.applicable_service_ids,
        applicable_service_names=package.applicable_service_names,
        applicable_employee_ids=package.applicable_employee_ids,
        applicable_store_ids=package.applicable_store_ids,
        allow_mixed_payment=package.allow_mixed_payment,
        description=package.description,
        status=package.status,
        created_at=package.created_at
    )


@router.put("/{package_no}", response_model=PackageCardResponse)
async def update_package_card(
    package_no: str,
    package_update: PackageCardUpdate,
    current_user: User = Depends(get_current_user)
):
    package = await PackageCard.find_one(PackageCard.package_no == package_no)
    if not package:
        raise HTTPException(status_code=404, detail="套餐不存在")

    update_data = package_update.model_dump(exclude_unset=True)

    if "name" in update_data and update_data["name"] != package.name:
        existing_name = await PackageCard.find_one(PackageCard.name == update_data["name"])
        if existing_name:
            raise HTTPException(status_code=400, detail="套餐名称已存在")

    if "applicable_service_ids" in update_data:
        services = await Service.find(Service.service_id.in_(update_data["applicable_service_ids"])).to_list()
        if len(services) != len(update_data["applicable_service_ids"]):
            raise HTTPException(status_code=400, detail="存在无效的服务项目编号")
        if "applicable_service_names" not in update_data:
            update_data["applicable_service_names"] = [s.name for s in services]

    for key, value in update_data.items():
        setattr(package, key, value)

    await package.save()

    await add_operation_log(
        operator=current_user.username,
        module="套餐管理",
        action="修改套餐",
        target_id=package.package_no,
        detail=f"修改套餐：{package.name}"
    )

    return PackageCardResponse(
        id=str(package.id),
        package_no=package.package_no,
        name=package.name,
        package_type=package.package_type,
        price=package.price,
        total_times=package.total_times,
        gift_times=package.gift_times,
        valid_days=package.valid_days,
        applicable_service_ids=package.applicable_service_ids,
        applicable_service_names=package.applicable_service_names,
        applicable_employee_ids=package.applicable_employee_ids,
        applicable_store_ids=package.applicable_store_ids,
        allow_mixed_payment=package.allow_mixed_payment,
        description=package.description,
        status=package.status,
        created_at=package.created_at
    )


@router.delete("/{package_no}")
async def delete_package_card(package_no: str, current_user: User = Depends(get_current_user)):
    package = await PackageCard.find_one(PackageCard.package_no == package_no)
    if not package:
        raise HTTPException(status_code=404, detail="套餐不存在")

    member_packages = await MemberPackage.find(MemberPackage.package_no == package_no).count()
    if member_packages > 0:
        raise HTTPException(status_code=400, detail=f"该套餐下还有 {member_packages} 个会员套餐在使用，无法删除")

    await package.delete()

    await add_operation_log(
        operator=current_user.username,
        module="套餐管理",
        action="删除套餐",
        target_id=package_no,
        detail=f"删除套餐：{package.name}"
    )

    return {"message": "删除成功"}


@router.post("/member/activate", response_model=MemberPackageResponse)
async def activate_member_package(
    data: MemberPackageCreate,
    current_user: User = Depends(get_current_user)
):
    member = await Member.find_one(Member.member_no == data.member_no)
    if not member:
        raise HTTPException(status_code=404, detail="会员不存在")
    if member.status != "正常":
        raise HTTPException(status_code=400, detail="该会员状态异常，无法开通套餐")

    package = await PackageCard.find_one(PackageCard.package_no == data.package_no)
    if not package:
        raise HTTPException(status_code=404, detail="套餐不存在")
    if package.status != "启用":
        raise HTTPException(status_code=400, detail="该套餐已禁用，无法开通")

    total_times = package.total_times + package.gift_times
    expire_date = datetime.now() + timedelta(days=package.valid_days)

    db_member_package = MemberPackage(
        member_package_no=await generate_member_package_no(),
        member_no=member.member_no,
        member_name=member.name,
        phone=member.phone,
        package_no=package.package_no,
        package_name=package.name,
        package_type=package.package_type,
        total_times=total_times,
        used_times=0,
        remaining_times=total_times,
        price=package.price,
        purchase_date=datetime.now(),
        expire_date=expire_date,
        applicable_service_ids=package.applicable_service_ids,
        applicable_service_names=package.applicable_service_names,
        applicable_employee_ids=package.applicable_employee_ids,
        allow_mixed_payment=package.allow_mixed_payment,
        status="生效中",
        operator=current_user.username,
        remark=data.remark
    )
    await db_member_package.insert()

    await add_operation_log(
        operator=current_user.username,
        module="会员套餐",
        action="开通套餐",
        target_id=db_member_package.member_package_no,
        detail=f"为会员 {member.name} 开通套餐：{package.name}，次数：{total_times}次，有效期至：{expire_date.strftime('%Y-%m-%d')}"
    )

    return MemberPackageResponse(
        id=str(db_member_package.id),
        member_package_no=db_member_package.member_package_no,
        member_no=db_member_package.member_no,
        member_name=db_member_package.member_name,
        phone=db_member_package.phone,
        package_no=db_member_package.package_no,
        package_name=db_member_package.package_name,
        package_type=db_member_package.package_type,
        total_times=db_member_package.total_times,
        used_times=db_member_package.used_times,
        remaining_times=db_member_package.remaining_times,
        price=db_member_package.price,
        purchase_date=db_member_package.purchase_date,
        expire_date=db_member_package.expire_date,
        applicable_service_ids=db_member_package.applicable_service_ids,
        applicable_service_names=db_member_package.applicable_service_names,
        applicable_employee_ids=db_member_package.applicable_employee_ids,
        allow_mixed_payment=db_member_package.allow_mixed_payment,
        status=db_member_package.status,
        operator=db_member_package.operator,
        remark=db_member_package.remark,
        created_at=db_member_package.created_at
    )


@router.post("/member/renew", response_model=MemberPackageResponse)
async def renew_member_package(
    data: MemberPackageRenew,
    current_user: User = Depends(get_current_user)
):
    member_package = await MemberPackage.find_one(MemberPackage.member_package_no == data.member_package_no)
    if not member_package:
        raise HTTPException(status_code=404, detail="会员套餐不存在")

    package = await PackageCard.find_one(PackageCard.package_no == member_package.package_no)
    if not package:
        raise HTTPException(status_code=404, detail="套餐规则不存在")
    if package.status != "启用":
        raise HTTPException(status_code=400, detail="该套餐已禁用，无法续费")

    member = await Member.find_one(Member.member_no == member_package.member_no)
    if not member or member.status != "正常":
        raise HTTPException(status_code=400, detail="会员状态异常，无法续费")

    add_times = package.total_times + package.gift_times
    member_package.total_times += add_times
    member_package.remaining_times += add_times

    now = datetime.now()
    if member_package.expire_date > now:
        member_package.expire_date = member_package.expire_date + timedelta(days=package.valid_days)
    else:
        member_package.expire_date = now + timedelta(days=package.valid_days)

    if member_package.status in ["已过期", "已作废"]:
        member_package.status = "生效中"

    if data.remark:
        member_package.remark = (member_package.remark or "") + f"\n续费备注：{data.remark}"

    await member_package.save()

    await add_operation_log(
        operator=current_user.username,
        module="会员套餐",
        action="续费套餐",
        target_id=member_package.member_package_no,
        detail=f"为会员 {member_package.member_name} 续费套餐：{member_package.package_name}，增加次数：{add_times}次"
    )

    return MemberPackageResponse(
        id=str(member_package.id),
        member_package_no=member_package.member_package_no,
        member_no=member_package.member_no,
        member_name=member_package.member_name,
        phone=member_package.phone,
        package_no=member_package.package_no,
        package_name=member_package.package_name,
        package_type=member_package.package_type,
        total_times=member_package.total_times,
        used_times=member_package.used_times,
        remaining_times=member_package.remaining_times,
        price=member_package.price,
        purchase_date=member_package.purchase_date,
        expire_date=member_package.expire_date,
        applicable_service_ids=member_package.applicable_service_ids,
        applicable_service_names=member_package.applicable_service_names,
        applicable_employee_ids=member_package.applicable_employee_ids,
        allow_mixed_payment=member_package.allow_mixed_payment,
        status=member_package.status,
        operator=member_package.operator,
        remark=member_package.remark,
        created_at=member_package.created_at
    )


@router.post("/member/{member_package_no}/status", response_model=MemberPackageResponse)
async def update_member_package_status(
    member_package_no: str,
    data: MemberPackageStatusUpdate,
    current_user: User = Depends(get_current_user)
):
    member_package = await MemberPackage.find_one(MemberPackage.member_package_no == member_package_no)
    if not member_package:
        raise HTTPException(status_code=404, detail="会员套餐不存在")

    if data.status not in ["生效中", "已冻结", "已作废"]:
        raise HTTPException(status_code=400, detail="无效的状态值")

    if data.status == "已作废" and member_package.status == "已作废":
        raise HTTPException(status_code=400, detail="套餐已作废")

    old_status = member_package.status
    member_package.status = data.status
    if data.remark:
        member_package.remark = (member_package.remark or "") + f"\n状态变更备注：{data.remark}"
    await member_package.save()

    action_map = {"生效中": "解冻", "已冻结": "冻结", "已作废": "作废"}
    await add_operation_log(
        operator=current_user.username,
        module="会员套餐",
        action=f"{action_map.get(data.status, '状态变更')}套餐",
        target_id=member_package.member_package_no,
        detail=f"会员套餐 {member_package.package_name} 状态从 {old_status} 变更为 {data.status}"
    )

    return MemberPackageResponse(
        id=str(member_package.id),
        member_package_no=member_package.member_package_no,
        member_no=member_package.member_no,
        member_name=member_package.member_name,
        phone=member_package.phone,
        package_no=member_package.package_no,
        package_name=member_package.package_name,
        package_type=member_package.package_type,
        total_times=member_package.total_times,
        used_times=member_package.used_times,
        remaining_times=member_package.remaining_times,
        price=member_package.price,
        purchase_date=member_package.purchase_date,
        expire_date=member_package.expire_date,
        applicable_service_ids=member_package.applicable_service_ids,
        applicable_service_names=member_package.applicable_service_names,
        applicable_employee_ids=member_package.applicable_employee_ids,
        allow_mixed_payment=member_package.allow_mixed_payment,
        status=member_package.status,
        operator=member_package.operator,
        remark=member_package.remark,
        created_at=member_package.created_at
    )


@router.get("/member/list", response_model=List[MemberPackageResponse])
async def get_member_packages(
    member_no: Optional[str] = Query(None, description="会员编号"),
    package_no: Optional[str] = Query(None, description="套餐编号"),
    status: Optional[str] = Query(None, description="状态"),
    current_user: User = Depends(get_current_user)
):
    query: dict = {}
    if member_no:
        query["member_no"] = member_no
    if package_no:
        query["package_no"] = package_no
    if status:
        query["status"] = status

    member_packages = await MemberPackage.find(query).sort("-created_at").to_list()

    result = []
    for mp in member_packages:
        mp = await check_and_update_package_expiry(mp)
        result.append(MemberPackageResponse(
            id=str(mp.id),
            member_package_no=mp.member_package_no,
            member_no=mp.member_no,
            member_name=mp.member_name,
            phone=mp.phone,
            package_no=mp.package_no,
            package_name=mp.package_name,
            package_type=mp.package_type,
            total_times=mp.total_times,
            used_times=mp.used_times,
            remaining_times=mp.remaining_times,
            price=mp.price,
            purchase_date=mp.purchase_date,
            expire_date=mp.expire_date,
            applicable_service_ids=mp.applicable_service_ids,
            applicable_service_names=mp.applicable_service_names,
            applicable_employee_ids=mp.applicable_employee_ids,
            allow_mixed_payment=mp.allow_mixed_payment,
            status=mp.status,
            operator=mp.operator,
            remark=mp.remark,
            created_at=mp.created_at
        ))

    return result


@router.get("/member/{member_no}/available", response_model=List[MemberPackageResponse])
async def get_available_member_packages(
    member_no: str,
    service_id: Optional[str] = Query(None, description="服务项目编号"),
    employee_id: Optional[str] = Query(None, description="员工编号"),
    current_user: User = Depends(get_current_user)
):
    member = await Member.find_one(Member.member_no == member_no)
    if not member:
        raise HTTPException(status_code=404, detail="会员不存在")

    now = datetime.now()
    query: dict = {
        "member_no": member_no,
        "status": "生效中",
        "remaining_times": {"$gt": 0},
        "expire_date": {"$gte": now}
    }

    member_packages = await MemberPackage.find(query).sort("-created_at").to_list()

    result = []
    for mp in member_packages:
        if service_id and mp.applicable_service_ids:
            if service_id not in mp.applicable_service_ids:
                continue
        if employee_id and mp.applicable_employee_ids:
            if employee_id not in mp.applicable_employee_ids:
                continue
        result.append(MemberPackageResponse(
            id=str(mp.id),
            member_package_no=mp.member_package_no,
            member_no=mp.member_no,
            member_name=mp.member_name,
            phone=mp.phone,
            package_no=mp.package_no,
            package_name=mp.package_name,
            package_type=mp.package_type,
            total_times=mp.total_times,
            used_times=mp.used_times,
            remaining_times=mp.remaining_times,
            price=mp.price,
            purchase_date=mp.purchase_date,
            expire_date=mp.expire_date,
            applicable_service_ids=mp.applicable_service_ids,
            applicable_service_names=mp.applicable_service_names,
            applicable_employee_ids=mp.applicable_employee_ids,
            allow_mixed_payment=mp.allow_mixed_payment,
            status=mp.status,
            operator=mp.operator,
            remark=mp.remark,
            created_at=mp.created_at
        ))

    return result


@router.get("/redemptions", response_model=List[PackageRedemptionResponse])
async def get_package_redemptions(
    member_no: Optional[str] = Query(None, description="会员编号"),
    member_package_no: Optional[str] = Query(None, description="会员套餐编号"),
    appointment_no: Optional[str] = Query(None, description="预约编号"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user)
):
    query: dict = {}
    if member_no:
        query["member_no"] = member_no
    if member_package_no:
        query["member_package_no"] = member_package_no
    if appointment_no:
        query["appointment_no"] = appointment_no
    if start_date:
        date_start = datetime.strptime(start_date, "%Y-%m-%d")
        query["created_at"] = {"$gte": date_start}
    if end_date:
        date_end = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        query.setdefault("created_at", {})
        query["created_at"]["$lte"] = date_end

    redemptions = await PackageRedemption.find(query).sort("-created_at").to_list()
    return [
        PackageRedemptionResponse(
            id=str(r.id),
            redemption_no=r.redemption_no,
            member_package_no=r.member_package_no,
            member_no=r.member_no,
            member_name=r.member_name,
            phone=r.phone,
            package_no=r.package_no,
            package_name=r.package_name,
            appointment_no=r.appointment_no,
            service_id=r.service_id,
            service_name=r.service_name,
            employee_id=r.employee_id,
            employee_name=r.employee_name,
            redeem_times=r.redeem_times,
            remaining_before=r.remaining_before,
            remaining_after=r.remaining_after,
            mixed_payment=r.mixed_payment,
            mixed_pay_amount=r.mixed_pay_amount,
            operator=r.operator,
            remark=r.remark,
            created_at=r.created_at
        ) for r in redemptions
    ]

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query
from datetime import datetime, timedelta

from app.models.appointment import Appointment
from app.models.schedule import Schedule
from app.models.usage import Usage
from app.models.consumable import Consumable, get_stock_status
from app.models.member import Member
from app.models.member_recharge import MemberRecharge
from app.models.member_consumption import MemberConsumption
from app.models.member_package import MemberPackage
from app.models.package_redemption import PackageRedemption
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter()


@router.get("/appointments/count")
async def get_appointment_stats(
    start_date: str = Query(None, description="开始日期"),
    end_date: str = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user)
):
    query = {}
    if start_date:
        query["appointment_date"] = {"$gte": start_date}
    if end_date:
        query["appointment_date"] = query.get("appointment_date", {})
        query["appointment_date"]["$lte"] = end_date
    
    appointments = await Appointment.find(query).to_list()
    
    status_count = {}
    for a in appointments:
        status_count[a.status] = status_count.get(a.status, 0) + 1
    
    return {
        "total": len(appointments),
        "by_status": status_count,
        "pending": status_count.get("待服务", 0),
        "completed": status_count.get("已完成", 0),
        "cancelled": status_count.get("已取消", 0)
    }


@router.get("/schedules/distribution")
async def get_schedule_distribution(
    start_date: str = Query(None, description="开始日期"),
    end_date: str = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user)
):
    query = {}
    if start_date:
        query["schedule_date"] = {"$gte": start_date}
    if end_date:
        query["schedule_date"] = query.get("schedule_date", {})
        query["schedule_date"]["$lte"] = end_date
    
    schedules = await Schedule.find(query).to_list()
    
    employee_dist = {}
    for s in schedules:
        key = f"{s.employee_name}({s.employee_id})"
        employee_dist[key] = employee_dist.get(key, 0) + 1
    
    date_dist = {}
    for s in schedules:
        date_dist[s.schedule_date] = date_dist.get(s.schedule_date, 0) + 1
    
    return {
        "total": len(schedules),
        "by_employee": employee_dist,
        "by_date": date_dist
    }


@router.get("/consumables/ranking")
async def get_consumable_ranking(
    start_date: str = Query(None, description="开始日期"),
    end_date: str = Query(None, description="结束日期"),
    top_n: int = Query(10, description="排名数量"),
    current_user: User = Depends(get_current_user)
):
    query = {}
    if start_date:
        query["usage_date"] = {"$gte": start_date}
    if end_date:
        query["usage_date"] = query.get("usage_date", {})
        query["usage_date"]["$lte"] = end_date
    
    usages = await Usage.find(query).to_list()
    
    consumable_usage = {}
    for u in usages:
        key = f"{u.consumable_name}({u.consumable_no})"
        consumable_usage[key] = consumable_usage.get(key, 0) + u.quantity
    
    sorted_usage = sorted(consumable_usage.items(), key=lambda x: x[1], reverse=True)
    top_items = sorted_usage[:top_n]
    
    return {
        "ranking": [{"name": k, "quantity": v, "rank": i + 1} for i, (k, v) in enumerate(top_items)]
    }


@router.get("/summary")
async def get_dashboard_summary(current_user: User = Depends(get_current_user)):
    today = datetime.now().strftime("%Y-%m-%d")
    
    today_appointments = await Appointment.find(Appointment.appointment_date == today).to_list()
    today_schedules = await Schedule.find(Schedule.schedule_date == today).to_list()
    total_appointments = await Appointment.find_all().count()
    total_schedules = await Schedule.find_all().count()
    
    status_count = {}
    appointments = await Appointment.find_all().to_list()
    for a in appointments:
        status_count[a.status] = status_count.get(a.status, 0) + 1
    
    low_stock_count = await Consumable.find(
        {"$expr": {"$lt": ["$stock_quantity", "$warning_threshold"]}, "status": "正常"}
    ).count()

    total_members = await Member.find(Member.status == "正常").count()
    all_members = await Member.find_all().to_list()
    total_balance = sum(m.balance for m in all_members)
    total_recharge_amount = sum(m.total_recharge for m in all_members)

    return {
        "today": {
            "appointments": len(today_appointments),
            "schedules": len(today_schedules)
        },
        "total": {
            "appointments": total_appointments,
            "schedules": total_schedules
        },
        "appointment_status": status_count,
        "low_stock_count": low_stock_count,
        "members": {
            "total_members": total_members,
            "total_balance": round(total_balance, 2),
            "total_recharge_amount": round(total_recharge_amount, 2)
        }
    }


@router.get("/consumables/low-stock")
async def get_low_stock_warning(
    current_user: User = Depends(get_current_user)
):
    query = {"$expr": {"$lt": ["$stock_quantity", "$warning_threshold"]}, "status": "正常"}

    consumables = await Consumable.find(query).sort("stock_quantity").to_list()
    result = []
    for c in consumables:
        result.append({
            "id": str(c.id),
            "consumable_no": c.consumable_no,
            "name": c.name,
            "stock_quantity": c.stock_quantity,
            "warning_threshold": c.warning_threshold,
            "unit": c.unit,
            "stock_status": get_stock_status(c.stock_quantity, c.warning_threshold),
            "status": c.status,
            "gap": c.warning_threshold - c.stock_quantity
        })
    return {
        "total": len(result),
        "items": result
    }


@router.get("/usages/7-day-trend")
async def get_usage_7day_trend(
    source_type: str = Query(None, description="来源类型(手工/自动扣减)，默认全部"),
    current_user: User = Depends(get_current_user)
):
    today = datetime.now()
    days = []
    trend_data = []
    auto_count = 0
    manual_count = 0

    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        days.append(date_str)

        query = {"usage_date": date_str}
        if source_type:
            query["source_type"] = source_type

        date_usages = await Usage.find(query).to_list()
        total_qty = sum(u.quantity for u in date_usages)
        auto_qty = sum(u.quantity for u in date_usages if u.source_type == "自动扣减")
        manual_qty = sum(u.quantity for u in date_usages if u.source_type == "手工")

        auto_count += auto_qty
        manual_count += manual_qty

        trend_data.append({
            "date": date_str,
            "label": date.strftime("%m-%d"),
            "total": total_qty,
            "自动扣减": auto_qty,
            "手工": manual_qty
        })

    return {
        "trend": trend_data,
        "summary": {
            "total": auto_count + manual_count,
            "auto_deduct": auto_count,
            "manual": manual_count
        }
    }


@router.get("/members/recharge-7-day-trend")
async def get_member_recharge_7day_trend(current_user: User = Depends(get_current_user)):
    today = datetime.now()
    trend_data = []
    total_recharge = 0
    total_gift = 0

    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        date_start = datetime.strptime(date_str, "%Y-%m-%d")
        date_end = date_start.replace(hour=23, minute=59, second=59)

        date_recharges = await MemberRecharge.find(
            {"created_at": {"$gte": date_start, "$lte": date_end}}
        ).to_list()
        day_recharge = sum(r.recharge_amount for r in date_recharges)
        day_gift = sum(r.gift_amount for r in date_recharges)
        total_recharge += day_recharge
        total_gift += day_gift

        trend_data.append({
            "date": date_str,
            "label": date.strftime("%m-%d"),
            "recharge_amount": round(day_recharge, 2),
            "gift_amount": round(day_gift, 2),
            "total": round(day_recharge + day_gift, 2),
            "count": len(date_recharges)
        })

    return {
        "trend": trend_data,
        "summary": {
            "total_recharge": round(total_recharge, 2),
            "total_gift": round(total_gift, 2),
            "grand_total": round(total_recharge + total_gift, 2)
        }
    }


@router.get("/members/consumption-ranking")
async def get_member_consumption_ranking(
    start_date: str = Query(None, description="开始日期"),
    end_date: str = Query(None, description="结束日期"),
    top_n: int = Query(10, description="排名数量"),
    current_user: User = Depends(get_current_user)
):
    query: dict = {}
    if start_date:
        date_start = datetime.strptime(start_date, "%Y-%m-%d")
        query["created_at"] = {"$gte": date_start}
    if end_date:
        date_end = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        query.setdefault("created_at", {})
        query["created_at"]["$lte"] = date_end

    consumptions = await MemberConsumption.find(query).to_list()

    member_consumption: Dict[str, Dict] = {}
    for c in consumptions:
        if not c.member_no:
            continue
        key = f"{c.member_name or '未知'}({c.member_no})"
        if key not in member_consumption:
            member_consumption[key] = {"total_amount": 0, "count": 0}
        member_consumption[key]["total_amount"] += c.actual_amount
        member_consumption[key]["count"] += 1

    sorted_items = sorted(
        member_consumption.items(),
        key=lambda x: x[1]["total_amount"],
        reverse=True
    )
    top_items = sorted_items[:top_n]

    return {
        "ranking": [
            {
                "name": k,
                "total_amount": round(v["total_amount"], 2),
                "count": v["count"],
                "rank": i + 1
            }
            for i, (k, v) in enumerate(top_items)
        ]
    }


@router.get("/packages/sales")
async def get_package_sales(
    start_date: str = Query(None, description="开始日期"),
    end_date: str = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user)
):
    query: dict = {}
    if start_date:
        date_start = datetime.strptime(start_date, "%Y-%m-%d")
        query["created_at"] = {"$gte": date_start}
    if end_date:
        date_end = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        query.setdefault("created_at", {})
        query["created_at"]["$lte"] = date_end

    member_packages = await MemberPackage.find(query).to_list()
    total_sales = sum(mp.price for mp in member_packages)
    package_stats: Dict[str, Dict] = {}
    for mp in member_packages:
        key = f"{mp.package_name}({mp.package_no})"
        if key not in package_stats:
            package_stats[key] = {"count": 0, "amount": 0}
        package_stats[key]["count"] += 1
        package_stats[key]["amount"] += mp.price

    sorted_packages = sorted(
        package_stats.items(),
        key=lambda x: x[1]["amount"],
        reverse=True
    )

    return {
        "total_count": len(member_packages),
        "total_sales": round(total_sales, 2),
        "by_package": [
            {
                "name": k,
                "count": v["count"],
                "amount": round(v["amount"], 2)
            }
            for k, v in sorted_packages
        ]
    }


@router.get("/packages/low-remaining-warning")
async def get_package_low_remaining_warning(
    threshold: int = Query(3, description="剩余次数预警阈值"),
    current_user: User = Depends(get_current_user)
):
    now = datetime.now()
    query: dict = {
        "status": "生效中",
        "remaining_times": {"$lte": threshold, "$gt": 0},
        "expire_date": {"$gte": now}
    }

    member_packages = await MemberPackage.find(query).sort("remaining_times").to_list()

    expiring_soon_date = now + timedelta(days=7)
    expiring_query: dict = {
        "status": "生效中",
        "expire_date": {"$gte": now, "$lte": expiring_soon_date},
        "remaining_times": {"$gt": 0}
    }
    expiring_packages = await MemberPackage.find(expiring_query).sort("expire_date").to_list()

    return {
        "low_remaining_total": len(member_packages),
        "low_remaining_items": [
            {
                "id": str(mp.id),
                "member_package_no": mp.member_package_no,
                "member_no": mp.member_no,
                "member_name": mp.member_name,
                "phone": mp.phone,
                "package_no": mp.package_no,
                "package_name": mp.package_name,
                "remaining_times": mp.remaining_times,
                "total_times": mp.total_times,
                "expire_date": mp.expire_date
            }
            for mp in member_packages
        ],
        "expiring_soon_total": len(expiring_packages),
        "expiring_soon_items": [
            {
                "id": str(mp.id),
                "member_package_no": mp.member_package_no,
                "member_no": mp.member_no,
                "member_name": mp.member_name,
                "phone": mp.phone,
                "package_no": mp.package_no,
                "package_name": mp.package_name,
                "remaining_times": mp.remaining_times,
                "expire_date": mp.expire_date,
                "days_left": (mp.expire_date - now).days
            }
            for mp in expiring_packages
        ]
    }


@router.get("/packages/redemption-7-day-trend")
async def get_package_redemption_7day_trend(current_user: User = Depends(get_current_user)):
    today = datetime.now()
    trend_data = []
    total_redemptions = 0
    total_mixed_pay_amount = 0

    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        date_start = datetime.strptime(date_str, "%Y-%m-%d")
        date_end = date_start.replace(hour=23, minute=59, second=59)

        date_redemptions = await PackageRedemption.find(
            {"created_at": {"$gte": date_start, "$lte": date_end}}
        ).to_list()
        day_count = len(date_redemptions)
        day_mixed_amount = sum(r.mixed_pay_amount or 0 for r in date_redemptions)
        total_redemptions += day_count
        total_mixed_pay_amount += day_mixed_amount

        package_dist: Dict[str, int] = {}
        for r in date_redemptions:
            key = r.package_name
            package_dist[key] = package_dist.get(key, 0) + 1

        trend_data.append({
            "date": date_str,
            "label": date.strftime("%m-%d"),
            "redemption_count": day_count,
            "mixed_pay_amount": round(day_mixed_amount, 2),
            "by_package": package_dist
        })

    return {
        "trend": trend_data,
        "summary": {
            "total_redemptions": total_redemptions,
            "total_mixed_pay_amount": round(total_mixed_pay_amount, 2)
        }
    }

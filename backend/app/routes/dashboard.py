from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query
from datetime import datetime, timedelta

from app.models.appointment import Appointment
from app.models.schedule import Schedule
from app.models.usage import Usage
from app.models.consumable import Consumable, get_stock_status
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
        {"$expr": {"$lt": ["$stock_quantity", "$warning_threshold"]}}
    ).count()

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
        "low_stock_count": low_stock_count
    }


@router.get("/consumables/low-stock")
async def get_low_stock_warning(
    status: str = Query(None, description="业务状态过滤"),
    current_user: User = Depends(get_current_user)
):
    query = {"$expr": {"$lt": ["$stock_quantity", "$warning_threshold"]}}
    if status:
        query["status"] = status

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

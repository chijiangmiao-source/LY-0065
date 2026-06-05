from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query
from datetime import datetime, timedelta

from app.models.appointment import Appointment
from app.models.schedule import Schedule
from app.models.usage import Usage
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
    
    return {
        "today": {
            "appointments": len(today_appointments),
            "schedules": len(today_schedules)
        },
        "total": {
            "appointments": total_appointments,
            "schedules": total_schedules
        },
        "appointment_status": status_count
    }

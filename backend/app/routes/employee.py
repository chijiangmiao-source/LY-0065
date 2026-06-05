from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from beanie.operators import Or

from app.models.employee import Employee, EmployeeCreate, EmployeeUpdate, EmployeeResponse
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter()


@router.post("", response_model=EmployeeResponse)
async def create_employee(employee: EmployeeCreate, current_user: User = Depends(get_current_user)):
    existing = await Employee.find_one(Employee.employee_id == employee.employee_id)
    if existing:
        raise HTTPException(status_code=400, detail="员工编号已存在")
    db_employee = Employee(**employee.model_dump())
    await db_employee.insert()
    return EmployeeResponse(
        id=str(db_employee.id),
        employee_id=db_employee.employee_id,
        name=db_employee.name,
        phone=db_employee.phone,
        position=db_employee.position,
        status=db_employee.status,
        created_at=db_employee.created_at
    )


@router.get("", response_model=List[EmployeeResponse])
async def get_employees(
    name: Optional[str] = Query(None, description="员工姓名"),
    position: Optional[str] = Query(None, description="职位"),
    status: Optional[str] = Query(None, description="状态"),
    current_user: User = Depends(get_current_user)
):
    query = {}
    if name:
        query["name"] = {"$regex": name, "$options": "i"}
    if position:
        query["position"] = {"$regex": position, "$options": "i"}
    if status:
        query["status"] = status
    
    employees = await Employee.find(query).to_list()
    return [
        EmployeeResponse(
            id=str(e.id),
            employee_id=e.employee_id,
            name=e.name,
            phone=e.phone,
            position=e.position,
            status=e.status,
            created_at=e.created_at
        ) for e in employees
    ]


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(employee_id: str, current_user: User = Depends(get_current_user)):
    employee = await Employee.find_one(Employee.employee_id == employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="员工不存在")
    return EmployeeResponse(
        id=str(employee.id),
        employee_id=employee.employee_id,
        name=employee.name,
        phone=employee.phone,
        position=employee.position,
        status=employee.status,
        created_at=employee.created_at
    )


@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(employee_id: str, employee_update: EmployeeUpdate, current_user: User = Depends(get_current_user)):
    employee = await Employee.find_one(Employee.employee_id == employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="员工不存在")
    
    update_data = employee_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(employee, key, value)
    
    await employee.save()
    return EmployeeResponse(
        id=str(employee.id),
        employee_id=employee.employee_id,
        name=employee.name,
        phone=employee.phone,
        position=employee.position,
        status=employee.status,
        created_at=employee.created_at
    )


@router.delete("/{employee_id}")
async def delete_employee(employee_id: str, current_user: User = Depends(get_current_user)):
    employee = await Employee.find_one(Employee.employee_id == employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="员工不存在")
    await employee.delete()
    return {"message": "删除成功"}

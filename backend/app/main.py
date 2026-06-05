from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db
from app.routes import auth, employee, service, appointment, schedule, consumable, usage, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(settings.MONGODB_URL, settings.MONGODB_DB_NAME)
    yield


app = FastAPI(title="理发店预约排班与耗材领用系统", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(employee.router, prefix="/api/employees", tags=["员工管理"])
app.include_router(service.router, prefix="/api/services", tags=["服务项目管理"])
app.include_router(appointment.router, prefix="/api/appointments", tags=["预约管理"])
app.include_router(schedule.router, prefix="/api/schedules", tags=["排班管理"])
app.include_router(consumable.router, prefix="/api/consumables", tags=["耗材管理"])
app.include_router(usage.router, prefix="/api/usages", tags=["领用登记"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["统计看板"])


@app.get("/")
async def root():
    return {"message": "理发店预约排班与耗材领用系统 API"}

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.models import User, Employee, Service, Appointment, Schedule, Consumable, Usage


async def init_db(mongodb_url: str, db_name: str):
    client = AsyncIOMotorClient(mongodb_url)
    await init_beanie(
        database=client[db_name],
        document_models=[User, Employee, Service, Appointment, Schedule, Consumable, Usage],
    )
    await User.ensure_indexes()
    await Employee.ensure_indexes()
    await Service.ensure_indexes()
    await Appointment.ensure_indexes()
    await Schedule.ensure_indexes()
    await Consumable.ensure_indexes()
    await Usage.ensure_indexes()

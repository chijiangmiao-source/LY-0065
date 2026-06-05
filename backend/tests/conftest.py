import pytest
from httpx import AsyncClient, ASGITransport
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from mongomock_motor import AsyncMongoMockClient

from app.main import app
from app.models import (
    User, Employee, Service, Appointment, Schedule, Consumable, Usage,
    ServiceConsumableTemplate, MemberLevel, Member, MemberRecharge,
    MemberConsumption, OperationLog, PackageCard, MemberPackage, PackageRedemption
)
from app.config import settings


@pytest.fixture(scope="module")
def event_loop():
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def test_db():
    client = AsyncMongoMockClient()
    db = client["test_barbershop"]
    await init_beanie(
        database=db,
        document_models=[
            User, Employee, Service, Appointment, Schedule, Consumable, Usage,
            ServiceConsumableTemplate, MemberLevel, Member, MemberRecharge,
            MemberConsumption, OperationLog, PackageCard, MemberPackage, PackageRedemption
        ],
    )
    yield db
    await client.close()


@pytest.fixture(scope="module")
async def client(test_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

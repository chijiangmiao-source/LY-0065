import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from app.models.appointment import Appointment, AppointmentCompleteRequest
from app.models.service import Service
from app.models.member import Member
from app.models.member_level import MemberLevel
from app.models.member_package import MemberPackage
from app.models.package_redemption import PackageRedemption
from app.models.consumable import Consumable
from app.models.service_consumable_template import ServiceConsumableTemplate
from app.models.usage import Usage
from app.models.member_consumption import MemberConsumption
from app.models.operation_log import OperationLog
from app.models.user import User

from app.services.exceptions import (
    ValidationException,
    InsufficientBalanceException,
    InsufficientStockException,
    PackageInvalidException,
)
from app.services.appointment_service import AppointmentService


def _make_appointment(**kwargs):
    defaults = dict(
        appointment_no="A001",
        customer_name="张三",
        phone="13800138000",
        service_id="S001",
        service_name="洗剪吹",
        employee_id="E001",
        employee_name="李师傅",
        appointment_date="2099-01-01",
        time_slot="10:00-11:00",
        status="待服务",
    )
    defaults.update(kwargs)
    return Appointment(**defaults)


def _make_service(**kwargs):
    defaults = dict(
        service_id="S001",
        name="洗剪吹",
        duration=60,
        price=100.0,
    )
    defaults.update(kwargs)
    return Service(**defaults)


def _make_member(**kwargs):
    defaults = dict(
        member_no="M001",
        name="张三",
        phone="13800138000",
        level_id="LV001",
        level_name="普通会员",
        balance=500.0,
        total_recharge=500.0,
        total_consumption=0.0,
        status="正常",
    )
    defaults.update(kwargs)
    return Member(**defaults)


def _make_member_level(**kwargs):
    defaults = dict(
        level_id="LV001",
        name="普通会员",
        min_recharge=0,
        discount_rate=0.9,
    )
    defaults.update(kwargs)
    return MemberLevel(**defaults)


def _make_member_package(**kwargs):
    defaults = dict(
        member_package_no="MP001",
        member_no="M001",
        member_name="张三",
        phone="13800138000",
        package_no="P001",
        package_name="洗剪吹10次卡",
        package_type="次卡",
        total_times=10,
        used_times=0,
        remaining_times=10,
        price=800.0,
        expire_date=datetime.now() + timedelta(days=365),
        applicable_service_ids=["S001"],
        applicable_service_names=["洗剪吹"],
        applicable_employee_ids=["E001"],
        allow_mixed_payment=True,
        status="生效中",
        operator="admin",
    )
    defaults.update(kwargs)
    return MemberPackage(**defaults)


@pytest.mark.asyncio
async def test_validate_appointment_for_complete_not_found():
    with patch.object(Appointment, "find_one", new_callable=AsyncMock) as mock_find:
        mock_find.return_value = None
        with pytest.raises(ValidationException, match="预约不存在"):
            await AppointmentService.validate_appointment_for_complete("A999")


@pytest.mark.asyncio
async def test_validate_appointment_for_complete_cancelled():
    apt = _make_appointment(status="已取消")
    with patch.object(Appointment, "find_one", new_callable=AsyncMock) as mock_find:
        mock_find.return_value = apt
        with pytest.raises(ValidationException, match="已取消的预约不能办理服务"):
            await AppointmentService.validate_appointment_for_complete("A001")


@pytest.mark.asyncio
async def test_validate_appointment_for_complete_already_done():
    apt = _make_appointment(status="已完成")
    with patch.object(Appointment, "find_one", new_callable=AsyncMock) as mock_find:
        mock_find.return_value = apt
        with pytest.raises(ValidationException, match="该预约已完成"):
            await AppointmentService.validate_appointment_for_complete("A001")


@pytest.mark.asyncio
async def test_validate_appointment_for_complete_success():
    apt = _make_appointment()
    with patch.object(Appointment, "find_one", new_callable=AsyncMock) as mock_find:
        mock_find.return_value = apt
        result = await AppointmentService.validate_appointment_for_complete("A001")
        assert result.appointment_no == "A001"


@pytest.mark.asyncio
async def test_get_service_for_appointment_not_found():
    with patch.object(Service, "find_one", new_callable=AsyncMock) as mock_find:
        mock_find.return_value = None
        with pytest.raises(ValidationException, match="服务项目不存在"):
            await AppointmentService.get_service_for_appointment("S999")


@pytest.mark.asyncio
async def test_get_service_for_appointment_success():
    svc = _make_service()
    with patch.object(Service, "find_one", new_callable=AsyncMock) as mock_find:
        mock_find.return_value = svc
        result = await AppointmentService.get_service_for_appointment("S001")
        assert result.service_id == "S001"
        assert result.price == 100.0


@pytest.mark.asyncio
@patch("app.services.payment_service.PaymentService")
@patch("app.services.package_service.PackageService")
@patch("app.services.consumable_service.ConsumableService")
@patch("app.services.consumption_service.ConsumptionService")
@patch("app.services.consumption_service.LogService")
@patch("app.services.number_service.NumberService")
async def test_complete_appointment_cash(
    mock_number, mock_log, mock_consumption, mock_consumable, mock_package, mock_payment
):
    apt = _make_appointment()
    svc = _make_service()

    mock_validate_apt = AsyncMock(return_value=apt)
    mock_get_svc = AsyncMock(return_value=svc)
    mock_consumable.deduct_consumables_for_service = AsyncMock(
        return_value=MagicMock(usages=[], updated_consumables=[])
    )
    mock_consumption.create_consumption_record = AsyncMock(return_value=MagicMock())
    mock_log.add_operation_log = AsyncMock(return_value=MagicMock())
    apt.save = AsyncMock()

    with patch.object(AppointmentService, "validate_appointment_for_complete", mock_validate_apt), \
         patch.object(AppointmentService, "get_service_for_appointment", mock_get_svc):

        request = AppointmentCompleteRequest(pay_method="现金")
        result = await AppointmentService.complete_appointment(
            appointment_no="A001",
            request_data=request,
            operator="admin",
        )

    assert "现金支付" in result.message
    assert result.pay_info["pay_method"] == "现金"
    assert result.pay_info["original_price"] == 100.0
    assert result.pay_info["actual_amount"] == 100.0
    assert result.pay_info["discount_rate"] == 1.0
    assert apt.status == "已完成"
    assert apt.pay_method == "现金"


@pytest.mark.asyncio
@patch("app.services.payment_service.PaymentService")
@patch("app.services.package_service.PackageService")
@patch("app.services.consumable_service.ConsumableService")
@patch("app.services.consumption_service.ConsumptionService")
@patch("app.services.consumption_service.LogService")
async def test_complete_appointment_balance(
    mock_log, mock_consumption, mock_consumable, mock_package, mock_payment
):
    apt = _make_appointment()
    svc = _make_service()
    member = _make_member()

    from app.services.payment_service import PaymentResult
    payment_result = PaymentResult(
        member=member,
        original_price=100.0,
        discount_rate=0.9,
        actual_amount=90.0,
        balance_before=500.0,
        balance_after=410.0,
    )

    mock_validate_apt = AsyncMock(return_value=apt)
    mock_get_svc = AsyncMock(return_value=svc)
    mock_payment.validate_member_for_payment = AsyncMock(return_value=member)
    mock_payment.process_balance_payment = AsyncMock(return_value=payment_result)
    mock_consumable.deduct_consumables_for_service = AsyncMock(
        return_value=MagicMock(usages=[], updated_consumables=[])
    )
    mock_consumption.create_consumption_record = AsyncMock(return_value=MagicMock())
    mock_log.add_operation_log = AsyncMock(return_value=MagicMock())
    apt.save = AsyncMock()

    with patch.object(AppointmentService, "validate_appointment_for_complete", mock_validate_apt), \
         patch.object(AppointmentService, "get_service_for_appointment", mock_get_svc):

        request = AppointmentCompleteRequest(pay_method="余额", member_no="M001")
        result = await AppointmentService.complete_appointment(
            appointment_no="A001",
            request_data=request,
            operator="admin",
        )

    assert "余额支付" in result.message
    assert result.pay_info["pay_method"] == "余额"
    assert result.pay_info["actual_amount"] == 90.0
    assert result.pay_info["balance_before"] == 500.0
    assert result.pay_info["balance_after"] == 410.0
    assert result.pay_info["discount_rate"] == 0.9


@pytest.mark.asyncio
@patch("app.services.payment_service.PaymentService")
@patch("app.services.package_service.PackageService")
@patch("app.services.consumable_service.ConsumableService")
@patch("app.services.consumption_service.ConsumptionService")
@patch("app.services.consumption_service.LogService")
async def test_complete_appointment_invalid_pay_method(
    mock_log, mock_consumption, mock_consumable, mock_package, mock_payment
):
    apt = _make_appointment()
    mock_validate_apt = AsyncMock(return_value=apt)

    with patch.object(AppointmentService, "validate_appointment_for_complete", mock_validate_apt):
        request = AppointmentCompleteRequest(pay_method="微信")
        with pytest.raises(ValidationException, match="支付方式必须为"):
            await AppointmentService.complete_appointment(
                appointment_no="A001",
                request_data=request,
                operator="admin",
            )


@pytest.mark.asyncio
@patch("app.services.consumable_service.ConsumableService")
@patch("app.services.consumption_service.LogService")
async def test_cancel_appointment_pending(mock_log, mock_consumable):
    apt = _make_appointment(status="待服务")
    mock_validate = AsyncMock(return_value=apt)
    mock_consumable.rollback_deductions = AsyncMock(return_value=([], 0))
    mock_log.add_operation_log = AsyncMock(return_value=MagicMock())
    apt.save = AsyncMock()

    with patch.object(AppointmentService, "validate_appointment_for_cancel", mock_validate):
        result = await AppointmentService.cancel_appointment("A001", "admin")

    assert "预约已取消" in result.message
    assert apt.status == "已取消"
    assert result.rolled_back["consumables_restored"] == 0


@pytest.mark.asyncio
async def test_cancel_appointment_not_found():
    with patch.object(Appointment, "find_one", new_callable=AsyncMock) as mock_find:
        mock_find.return_value = None
        with pytest.raises(ValidationException, match="预约不存在"):
            await AppointmentService.validate_appointment_for_cancel("A999")


@pytest.mark.asyncio
async def test_cancel_appointment_already_cancelled():
    apt = _make_appointment(status="已取消")
    with patch.object(Appointment, "find_one", new_callable=AsyncMock) as mock_find:
        mock_find.return_value = apt
        with pytest.raises(ValidationException, match="预约已取消"):
            await AppointmentService.validate_appointment_for_cancel("A001")

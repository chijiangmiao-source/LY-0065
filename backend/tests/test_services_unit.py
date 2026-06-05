import pytest
from datetime import datetime, timedelta

from app.services.exceptions import (
    BusinessException,
    ValidationException,
    InsufficientBalanceException,
    InsufficientStockException,
    PackageInvalidException,
)
from app.services.number_service import NumberService
from app.services.payment_service import PaymentService
from app.services.appointment_service import AppointmentService


class TestBusinessExceptions:
    def test_business_exception_defaults(self):
        exc = BusinessException("test error")
        assert exc.message == "test error"
        assert exc.status_code == 400
        assert exc.detail is None

    def test_business_exception_with_detail(self):
        exc = BusinessException("test", detail={"key": "value"}, status_code=404)
        assert exc.message == "test"
        assert exc.status_code == 404
        assert exc.detail == {"key": "value"}

    def test_validation_exception(self):
        exc = ValidationException("validation failed")
        assert exc.status_code == 400
        assert isinstance(exc, BusinessException)

    def test_insufficient_balance_exception(self):
        exc = InsufficientBalanceException(
            "not enough", current_balance=10.0, required=50.0
        )
        assert exc.status_code == 400
        assert exc.detail == {"current_balance": 10.0, "required": 50.0}

    def test_insufficient_balance_exception_no_details(self):
        exc = InsufficientBalanceException("not enough")
        assert exc.detail is None

    def test_insufficient_stock_exception(self):
        items = ["item1", "item2"]
        exc = InsufficientStockException("stock out", insufficient_items=items)
        assert exc.status_code == 400
        assert exc.detail == {"insufficient_items": items}

    def test_package_invalid_exception(self):
        exc = PackageInvalidException("package expired")
        assert exc.status_code == 400
        assert isinstance(exc, BusinessException)


class TestNumberService:
    @pytest.mark.asyncio
    async def test_number_formats(self):
        usage_no = await NumberService.generate_usage_no()
        assert usage_no.startswith("LY")
        assert len(usage_no) >= 12

        consumption_no = await NumberService.generate_consumption_no()
        assert consumption_no.startswith("C")

        log_id = await NumberService.generate_log_id()
        assert log_id.startswith("LOG")

        member_no = await NumberService.generate_member_no()
        assert member_no.startswith("M")

        recharge_no = await NumberService.generate_recharge_no()
        assert recharge_no.startswith("R")

        member_pkg_no = await NumberService.generate_member_package_no()
        assert member_pkg_no.startswith("MP")

        package_no = await NumberService.generate_package_no()
        assert package_no.startswith("P")

        redemption_no = await NumberService.generate_redemption_no()
        assert redemption_no.startswith("R")


class TestAppointmentServiceTimeValidation:
    def test_valid_future_time(self):
        future_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        assert AppointmentService.is_time_valid(future_date, "10:00-11:00") is True

    def test_invalid_past_time(self):
        past_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        assert AppointmentService.is_time_valid(past_date, "10:00-11:00") is False

    def test_invalid_format_handled_gracefully(self):
        assert AppointmentService.is_time_valid("invalid", "invalid") is True

    def test_valid_today_future_slot(self):
        today = datetime.now()
        future_hour = (today + timedelta(hours=2)).hour
        date_str = today.strftime("%Y-%m-%d")
        time_slot = f"{future_hour:02d}:00-{future_hour+1:02d}:00"
        assert AppointmentService.is_time_valid(date_str, time_slot) is True

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta

from app.models.member import Member
from app.models.member_level import MemberLevel
from app.models.member_package import MemberPackage

from app.services.exceptions import (
    ValidationException,
    InsufficientBalanceException,
    PackageInvalidException,
)
from app.services.payment_service import PaymentService
from app.services.package_service import PackageService


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


class TestPaymentService:
    @pytest.mark.asyncio
    async def test_get_member_discount_with_level(self):
        member = _make_member()
        level = _make_member_level()
        with patch.object(MemberLevel, "find_one", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = level
            rate = await PaymentService.get_member_discount(member)
            assert rate == 0.9

    @pytest.mark.asyncio
    async def test_get_member_discount_no_level(self):
        member = _make_member()
        with patch.object(MemberLevel, "find_one", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = None
            rate = await PaymentService.get_member_discount(member)
            assert rate == 1.0

    @pytest.mark.asyncio
    async def test_validate_member_no_member_no(self):
        with pytest.raises(ValidationException, match="余额支付必须选择会员"):
            await PaymentService.validate_member_for_payment(None)

    @pytest.mark.asyncio
    async def test_validate_member_not_found(self):
        with patch.object(Member, "find_one", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = None
            with pytest.raises(ValidationException, match="会员不存在"):
                await PaymentService.validate_member_for_payment("M999")

    @pytest.mark.asyncio
    async def test_validate_member_phone_mismatch(self):
        member = _make_member()
        with patch.object(Member, "find_one", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = member
            with pytest.raises(ValidationException, match="会员手机号与预约手机号不一致"):
                await PaymentService.validate_member_for_payment("M001", expected_phone="13900139000")

    @pytest.mark.asyncio
    async def test_validate_member_abnormal_status(self):
        member = _make_member(status="已冻结")
        with patch.object(Member, "find_one", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = member
            with pytest.raises(ValidationException, match="该会员状态异常"):
                await PaymentService.validate_member_for_payment("M001")

    @pytest.mark.asyncio
    async def test_validate_member_success(self):
        member = _make_member()
        with patch.object(Member, "find_one", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = member
            result = await PaymentService.validate_member_for_payment("M001", expected_phone="13800138000")
            assert result.member_no == "M001"

    @pytest.mark.asyncio
    async def test_process_balance_payment_insufficient(self):
        member = _make_member(balance=10.0)
        level = _make_member_level()
        with patch.object(MemberLevel, "find_one", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = level
            with pytest.raises(InsufficientBalanceException):
                await PaymentService.process_balance_payment(member, 100.0)

    @pytest.mark.asyncio
    async def test_process_balance_payment_success(self):
        member = _make_member(balance=500.0, total_consumption=0.0)
        level = _make_member_level(discount_rate=0.9)
        member.save = AsyncMock()
        with patch.object(MemberLevel, "find_one", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = level
            result = await PaymentService.process_balance_payment(member, 100.0)

        assert result.original_price == 100.0
        assert result.discount_rate == 0.9
        assert result.actual_amount == 90.0
        assert result.balance_before == 500.0
        assert result.balance_after == 410.0
        assert member.balance == 410.0
        assert member.total_consumption == 90.0

    @pytest.mark.asyncio
    async def test_refund_balance(self):
        member = _make_member(balance=410.0, total_consumption=90.0)
        member.save = AsyncMock()
        before, after = await PaymentService.refund_balance(member, 90.0)
        assert before == 410.0
        assert after == 500.0
        assert member.balance == 500.0
        assert member.total_consumption == 0.0


class TestPackageService:
    @pytest.mark.asyncio
    async def test_validate_member_for_package_not_found(self):
        with patch.object(Member, "find_one", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = None
            with pytest.raises(ValidationException, match="会员不存在"):
                await PackageService.validate_member_for_package("M999")

    @pytest.mark.asyncio
    async def test_validate_member_for_package_abnormal(self):
        member = _make_member(status="已冻结")
        with patch.object(Member, "find_one", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = member
            with pytest.raises(PackageInvalidException, match="该会员状态异常"):
                await PackageService.validate_member_for_package("M001")

    @pytest.mark.asyncio
    async def test_validate_member_package_not_found(self):
        with patch.object(MemberPackage, "find_one", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = None
            with pytest.raises(PackageInvalidException, match="会员套餐不存在"):
                await PackageService.validate_member_package("MP999", "M001")

    @pytest.mark.asyncio
    async def test_validate_member_package_wrong_member(self):
        pkg = _make_member_package(member_no="M002")
        with patch.object(MemberPackage, "find_one", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = pkg
            with pytest.raises(PackageInvalidException, match="该套餐不属于所选会员"):
                await PackageService.validate_member_package("MP001", "M001")

    @pytest.mark.asyncio
    async def test_validate_member_package_inactive(self):
        pkg = _make_member_package(status="已冻结")
        with patch.object(MemberPackage, "find_one", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = pkg
            with pytest.raises(PackageInvalidException, match="套餐状态异常"):
                await PackageService.validate_member_package("MP001", "M001")

    @pytest.mark.asyncio
    async def test_validate_member_package_expired(self):
        pkg = _make_member_package(expire_date=datetime.now() - timedelta(days=1))
        with patch.object(MemberPackage, "find_one", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = pkg
            with pytest.raises(PackageInvalidException, match="过期"):
                await PackageService.validate_member_package("MP001", "M001")

    @pytest.mark.asyncio
    async def test_validate_member_package_no_remaining(self):
        pkg = _make_member_package(remaining_times=0)
        with patch.object(MemberPackage, "find_one", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = pkg
            with pytest.raises(PackageInvalidException, match="剩余次数不足"):
                await PackageService.validate_member_package("MP001", "M001")

    @pytest.mark.asyncio
    async def test_validate_member_package_service_mismatch(self):
        pkg = _make_member_package(applicable_service_ids=["S002"])
        with patch.object(MemberPackage, "find_one", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = pkg
            with pytest.raises(PackageInvalidException, match="当前服务不匹配"):
                await PackageService.validate_member_package("MP001", "M001", service_id="S001")

    @pytest.mark.asyncio
    async def test_validate_member_package_employee_mismatch(self):
        pkg = _make_member_package(applicable_employee_ids=["E002"])
        with patch.object(MemberPackage, "find_one", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = pkg
            with pytest.raises(PackageInvalidException, match="不支持当前服务员工"):
                await PackageService.validate_member_package(
                    "MP001", "M001", service_id="S001", employee_id="E001"
                )

    @pytest.mark.asyncio
    async def test_validate_member_package_success(self):
        pkg = _make_member_package()
        with patch.object(MemberPackage, "find_one", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = pkg
            result = await PackageService.validate_member_package(
                "MP001", "M001", service_id="S001", employee_id="E001"
            )
            assert result.member_package_no == "MP001"

from datetime import datetime
from typing import Optional, Tuple
from dataclasses import dataclass

from app.models.member import Member
from app.models.member_package import MemberPackage
from app.models.package_redemption import PackageRedemption
from app.models.appointment import Appointment
from app.services.number_service import NumberService
from app.services.exceptions import (
    ValidationException,
    PackageInvalidException,
    InsufficientBalanceException,
)
from app.services.payment_service import PaymentService


@dataclass
class RedemptionResult:
    member_package: MemberPackage
    member: Member
    remaining_before: int
    remaining_after: int
    mixed_payment: bool
    mixed_pay_amount: Optional[float]
    balance_before: Optional[float]
    balance_after: Optional[float]
    redemption: PackageRedemption
    discount_rate: float


class PackageService:
    @staticmethod
    async def validate_member_for_package(
        member_no: str,
        expected_phone: Optional[str] = None,
    ) -> Member:
        member = await Member.find_one(Member.member_no == member_no)
        if not member:
            raise ValidationException("会员不存在")

        if expected_phone and member.phone != expected_phone:
            raise ValidationException("会员手机号与预约手机号不一致")

        if member.status != "正常":
            raise PackageInvalidException("该会员状态异常，无法使用次卡")

        return member

    @staticmethod
    async def validate_member_package(
        member_package_no: str,
        member_no: str,
        service_id: Optional[str] = None,
        employee_id: Optional[str] = None,
    ) -> MemberPackage:
        member_package = await MemberPackage.find_one(
            MemberPackage.member_package_no == member_package_no
        )
        if not member_package:
            raise PackageInvalidException("会员套餐不存在")

        if member_package.member_no != member_no:
            raise PackageInvalidException("该套餐不属于所选会员")

        if member_package.status != "生效中":
            raise PackageInvalidException(
                f"套餐状态异常：{member_package.status}，无法核销"
            )

        if member_package.expire_date < datetime.now():
            raise PackageInvalidException(
                f"套餐已于 {member_package.expire_date.strftime('%Y-%m-%d')} 过期，无法核销"
            )

        if member_package.remaining_times < 1:
            raise PackageInvalidException("套餐剩余次数不足，无法核销")

        if service_id and member_package.applicable_service_ids:
            if service_id not in member_package.applicable_service_ids:
                raise PackageInvalidException(
                    f"该套餐仅适用于：{', '.join(member_package.applicable_service_names)}，当前服务不匹配"
                )

        if employee_id and member_package.applicable_employee_ids:
            if employee_id not in member_package.applicable_employee_ids:
                raise PackageInvalidException("该套餐不支持当前服务员工")

        return member_package

    @staticmethod
    async def process_package_redemption(
        member: Member,
        member_package: MemberPackage,
        appointment: Appointment,
        use_mixed_payment: bool = False,
        original_price: float = 0.0,
        operator: str = "",
    ) -> RedemptionResult:
        if use_mixed_payment and not member_package.allow_mixed_payment:
            raise PackageInvalidException("该套餐不支持与余额混合支付")

        remaining_before = member_package.remaining_times
        member_package.used_times += 1
        member_package.remaining_times -= 1
        remaining_after = member_package.remaining_times

        mixed_payment = False
        mixed_pay_amount = None
        balance_before = None
        balance_after = None
        discount_rate = 1.0

        if use_mixed_payment:
            discount_rate = await PaymentService.get_member_discount(member)
            mixed_pay_amount = round(original_price * discount_rate, 2)

            if member.balance < mixed_pay_amount:
                raise InsufficientBalanceException(
                    f"混合支付余额不足，当前余额：{member.balance} 元，需支付：{mixed_pay_amount} 元",
                    current_balance=member.balance,
                    required=mixed_pay_amount,
                )

            balance_before = member.balance
            balance_after = round(member.balance - mixed_pay_amount, 2)
            member.balance = balance_after
            member.total_consumption += mixed_pay_amount
            mixed_payment = True

        await member_package.save()
        if mixed_payment:
            await member.save()

        redemption = PackageRedemption(
            redemption_no=await NumberService.generate_redemption_no(),
            member_package_no=member_package.member_package_no,
            member_no=member.member_no,
            member_name=member.name,
            phone=member.phone,
            package_no=member_package.package_no,
            package_name=member_package.package_name,
            appointment_no=appointment.appointment_no,
            service_id=appointment.service_id,
            service_name=appointment.service_name,
            employee_id=appointment.employee_id,
            employee_name=appointment.employee_name,
            redeem_times=1,
            remaining_before=remaining_before,
            remaining_after=remaining_after,
            mixed_payment=mixed_payment,
            mixed_pay_amount=mixed_pay_amount,
            operator=operator,
            remark=f"预约服务完成次卡核销",
        )
        await redemption.insert()

        return RedemptionResult(
            member_package=member_package,
            member=member,
            remaining_before=remaining_before,
            remaining_after=remaining_after,
            mixed_payment=mixed_payment,
            mixed_pay_amount=mixed_pay_amount,
            balance_before=balance_before,
            balance_after=balance_after,
            redemption=redemption,
            discount_rate=discount_rate,
        )

    @staticmethod
    async def rollback_redemption(
        appointment_no: str,
    ) -> Tuple[Optional[MemberPackage], Optional[Member]]:
        redemption = await PackageRedemption.find_one(
            PackageRedemption.appointment_no == appointment_no
        )
        if not redemption:
            return None, None

        member_package = await MemberPackage.find_one(
            MemberPackage.member_package_no == redemption.member_package_no
        )
        member = None

        if member_package and member_package.status == "生效中":
            member_package.used_times = max(
                0, member_package.used_times - redemption.redeem_times
            )
            member_package.remaining_times += redemption.redeem_times
            await member_package.save()

            if redemption.mixed_payment and redemption.mixed_pay_amount:
                member = await Member.find_one(Member.member_no == redemption.member_no)
                if member:
                    member.balance = round(
                        member.balance + redemption.mixed_pay_amount, 2
                    )
                    member.total_consumption = max(
                        0, member.total_consumption - redemption.mixed_pay_amount
                    )
                    await member.save()

        await redemption.delete()
        return member_package, member

from typing import Optional, Tuple
from dataclasses import dataclass

from app.models.member import Member
from app.models.member_level import MemberLevel
from app.services.exceptions import (
    ValidationException,
    InsufficientBalanceException,
)


@dataclass
class PaymentResult:
    member: Member
    original_price: float
    discount_rate: float
    actual_amount: float
    balance_before: float
    balance_after: float


class PaymentService:
    @staticmethod
    async def get_member_discount(member: Member) -> float:
        level = await MemberLevel.find_one(MemberLevel.level_id == member.level_id)
        return level.discount_rate if level else 1.0

    @staticmethod
    async def validate_member_for_payment(
        member_no: Optional[str],
        expected_phone: Optional[str] = None,
    ) -> Member:
        if not member_no:
            raise ValidationException("余额支付必须选择会员")

        member = await Member.find_one(Member.member_no == member_no)
        if not member:
            raise ValidationException("会员不存在")

        if expected_phone and member.phone != expected_phone:
            raise ValidationException("会员手机号与预约手机号不一致")

        if member.status != "正常":
            raise ValidationException("该会员状态异常，无法使用余额支付")

        return member

    @staticmethod
    async def process_balance_payment(
        member: Member,
        original_price: float,
    ) -> PaymentResult:
        discount_rate = await PaymentService.get_member_discount(member)
        actual_amount = round(original_price * discount_rate, 2)

        if member.balance < actual_amount:
            raise InsufficientBalanceException(
                f"会员余额不足，当前余额：{member.balance} 元，需支付：{actual_amount} 元",
                current_balance=member.balance,
                required=actual_amount,
            )

        balance_before = member.balance
        balance_after = round(member.balance - actual_amount, 2)

        member.balance = balance_after
        member.total_consumption += actual_amount
        await member.save()

        return PaymentResult(
            member=member,
            original_price=original_price,
            discount_rate=discount_rate,
            actual_amount=actual_amount,
            balance_before=balance_before,
            balance_after=balance_after,
        )

    @staticmethod
    async def refund_balance(
        member: Member,
        amount: float,
    ) -> Tuple[float, float]:
        balance_before = member.balance
        balance_after = round(member.balance + amount, 2)
        member.balance = balance_after
        member.total_consumption = max(0, member.total_consumption - amount)
        await member.save()
        return balance_before, balance_after

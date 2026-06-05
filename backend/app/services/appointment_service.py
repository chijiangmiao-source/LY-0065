from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from app.models.appointment import Appointment, AppointmentCompleteRequest
from app.models.service import Service
from app.models.member import Member
from app.services.exceptions import (
    ValidationException,
    BusinessException,
)
from app.services.payment_service import PaymentService, PaymentResult
from app.services.package_service import PackageService, RedemptionResult
from app.services.consumable_service import (
    ConsumableService,
    ConsumableDeductionResult,
    StockCheckResult,
)
from app.services.consumption_service import ConsumptionService, LogService


@dataclass
class CompleteAppointmentResult:
    message: str
    pay_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CancelAppointmentResult:
    message: str
    rolled_back: Dict[str, Any] = field(default_factory=dict)


class AppointmentService:
    @staticmethod
    def is_time_valid(appointment_date: str, time_slot: str) -> bool:
        try:
            now = datetime.now()
            appointment_str = f"{appointment_date} {time_slot.split('-')[0]}"
            appointment_dt = datetime.strptime(appointment_str, "%Y-%m-%d %H:%M")
            return appointment_dt >= now
        except Exception:
            return True

    @staticmethod
    async def validate_appointment_for_complete(
        appointment_no: str,
    ) -> Appointment:
        appointment = await Appointment.find_one(
            Appointment.appointment_no == appointment_no
        )
        if not appointment:
            raise ValidationException("预约不存在")
        if appointment.status == "已取消":
            raise ValidationException("已取消的预约不能办理服务")
        if appointment.status == "已完成":
            raise ValidationException("该预约已完成")
        return appointment

    @staticmethod
    async def validate_appointment_for_cancel(
        appointment_no: str,
    ) -> Appointment:
        appointment = await Appointment.find_one(
            Appointment.appointment_no == appointment_no
        )
        if not appointment:
            raise ValidationException("预约不存在")
        if appointment.status == "已取消":
            raise ValidationException("预约已取消")
        return appointment

    @staticmethod
    async def get_service_for_appointment(
        service_id: str,
    ) -> Service:
        service = await Service.find_one(Service.service_id == service_id)
        if not service:
            raise ValidationException("服务项目不存在")
        return service

    @staticmethod
    async def check_stock(
        appointment_no: str,
    ) -> StockCheckResult:
        appointment = await Appointment.find_one(
            Appointment.appointment_no == appointment_no
        )
        if not appointment:
            raise ValidationException("预约不存在")
        return await ConsumableService.check_stock(appointment.service_id)

    @staticmethod
    async def _build_pay_detail(
        pay_method: str,
        actual_amount: float,
        original_price: float,
        discount_rate: float,
        redemption_info: Optional[Dict[str, Any]],
    ) -> str:
        if pay_method == "次卡":
            package_name = redemption_info.get("package_name", "") if redemption_info else ""
            remaining_after = redemption_info.get("remaining_after", 0) if redemption_info else 0
            mixed_payment = redemption_info.get("mixed_payment", False) if redemption_info else False
            mixed_pay_amount = redemption_info.get("mixed_pay_amount") if redemption_info else None

            pay_detail = f"次卡核销（{package_name}），剩余次数：{remaining_after}次"
            if mixed_payment and mixed_pay_amount:
                pay_detail += f"，混合余额支付 {mixed_pay_amount} 元"
        else:
            pay_detail = f"{pay_method}支付 {actual_amount} 元"
            if discount_rate < 1.0:
                pay_detail += f"（原价 {original_price} 元，折扣 {(discount_rate * 10):.1f} 折）"
        return pay_detail

    @staticmethod
    async def complete_appointment(
        appointment_no: str,
        request_data: AppointmentCompleteRequest,
        operator: str,
    ) -> CompleteAppointmentResult:
        appointment = await AppointmentService.validate_appointment_for_complete(
            appointment_no
        )

        if request_data.pay_method not in ["余额", "现金", "次卡"]:
            raise ValidationException("支付方式必须为'余额'、'现金'或'次卡'")

        service = await AppointmentService.get_service_for_appointment(
            appointment.service_id
        )
        original_price = service.price

        member: Optional[Member] = None
        discount_rate = 1.0
        balance_before: Optional[float] = None
        balance_after: Optional[float] = None
        actual_amount = 0.0
        redemption_info: Optional[Dict[str, Any]] = None
        payment_result: Optional[PaymentResult] = None
        redemption_result: Optional[RedemptionResult] = None

        if request_data.pay_method == "次卡":
            if not request_data.member_no:
                raise ValidationException("次卡核销必须选择会员")
            if not request_data.member_package_no:
                raise ValidationException("次卡核销必须选择会员套餐")

            member = await PackageService.validate_member_for_package(
                request_data.member_no,
                expected_phone=appointment.phone,
            )

            member_package = await PackageService.validate_member_package(
                member_package_no=request_data.member_package_no,
                member_no=request_data.member_no,
                service_id=appointment.service_id,
                employee_id=appointment.employee_id,
            )

            redemption_result = await PackageService.process_package_redemption(
                member=member,
                member_package=member_package,
                appointment=appointment,
                use_mixed_payment=request_data.use_mixed_payment or False,
                original_price=original_price,
                operator=operator,
            )

            discount_rate = redemption_result.discount_rate
            actual_amount = redemption_result.mixed_pay_amount or 0.0
            balance_before = redemption_result.balance_before
            balance_after = redemption_result.balance_after

            redemption_info = {
                "member_package_no": member_package.member_package_no,
                "package_name": member_package.package_name,
                "remaining_before": redemption_result.remaining_before,
                "remaining_after": redemption_result.remaining_after,
                "mixed_payment": redemption_result.mixed_payment,
                "mixed_pay_amount": redemption_result.mixed_pay_amount,
            }

        elif request_data.pay_method == "余额":
            member = await PaymentService.validate_member_for_payment(
                request_data.member_no,
                expected_phone=appointment.phone,
            )
            payment_result = await PaymentService.process_balance_payment(
                member, original_price
            )
            discount_rate = payment_result.discount_rate
            actual_amount = payment_result.actual_amount
            balance_before = payment_result.balance_before
            balance_after = payment_result.balance_after
        else:
            actual_amount = original_price

        try:
            deduction_result = await ConsumableService.deduct_consumables_for_service(
                service_id=appointment.service_id,
                appointment_no=appointment.appointment_no,
                service_name=appointment.service_name,
                employee_id=appointment.employee_id,
                employee_name=appointment.employee_name,
                operator_name=operator,
            )
        except BusinessException:
            if redemption_result:
                await PackageService.rollback_redemption(appointment.appointment_no)
            elif payment_result:
                await PaymentService.refund_balance(
                    payment_result.member, payment_result.actual_amount
                )
            raise

        try:
            await ConsumptionService.create_consumption_record(
                member_no=request_data.member_no,
                member_name=member.name if member else None,
                phone=member.phone if member else appointment.phone,
                appointment_no=appointment.appointment_no,
                service_id=appointment.service_id,
                service_name=appointment.service_name,
                original_price=original_price,
                discount_rate=discount_rate,
                actual_amount=actual_amount,
                pay_method=request_data.pay_method,
                balance_before=balance_before,
                balance_after=balance_after,
                operator=operator,
                remark=f"预约服务完成支付{'（次卡核销）' if request_data.pay_method == '次卡' else ''}",
            )
        except Exception:
            if deduction_result.usages:
                await ConsumableService.rollback_deductions(appointment.appointment_no)
            if redemption_result:
                await PackageService.rollback_redemption(appointment.appointment_no)
            elif payment_result:
                await PaymentService.refund_balance(
                    payment_result.member, payment_result.actual_amount
                )
            raise

        appointment.status = "已完成"
        appointment.pay_method = request_data.pay_method
        appointment.member_no = request_data.member_no
        appointment.pay_amount = actual_amount
        appointment.discount_rate = discount_rate
        await appointment.save()

        pay_detail = await AppointmentService._build_pay_detail(
            request_data.pay_method,
            actual_amount,
            original_price,
            discount_rate,
            redemption_info,
        )

        await LogService.add_operation_log(
            operator=operator,
            module="预约服务",
            action="完成服务",
            target_id=appointment.appointment_no,
            detail=f"完成预约服务 {appointment.customer_name} - {appointment.service_name}，{pay_detail}",
        )

        return CompleteAppointmentResult(
            message=f"服务已完成，耗材已自动扣减，{pay_detail}",
            pay_info={
                "pay_method": request_data.pay_method,
                "original_price": original_price,
                "discount_rate": discount_rate,
                "actual_amount": actual_amount,
                "balance_before": balance_before,
                "balance_after": balance_after,
                "redemption": redemption_info,
            },
        )

    @staticmethod
    async def cancel_appointment(
        appointment_no: str,
        operator: str,
    ) -> CancelAppointmentResult:
        appointment = await AppointmentService.validate_appointment_for_cancel(
            appointment_no
        )

        rolled_back: Dict[str, Any] = {
            "consumables_restored": 0,
            "package_restored": False,
            "balance_refunded": 0.0,
            "consumption_deleted": False,
        }

        if appointment.status == "已完成":
            _, count = await ConsumableService.rollback_deductions(appointment_no)
            rolled_back["consumables_restored"] = count

            if appointment.pay_method == "次卡":
                member_package, member = await PackageService.rollback_redemption(
                    appointment_no
                )
                rolled_back["package_restored"] = member_package is not None
                if member and appointment.pay_amount:
                    rolled_back["balance_refunded"] = appointment.pay_amount or 0.0

                await ConsumptionService.delete_consumption_by_appointment(
                    appointment_no
                )
                rolled_back["consumption_deleted"] = True

            if appointment.pay_method == "余额" and appointment.member_no and appointment.pay_amount:
                member = await Member.find_one(Member.member_no == appointment.member_no)
                if member:
                    _, _ = await PaymentService.refund_balance(
                        member, appointment.pay_amount
                    )
                    rolled_back["balance_refunded"] = appointment.pay_amount

                await ConsumptionService.delete_consumption_by_appointment(
                    appointment_no
                )
                rolled_back["consumption_deleted"] = True

        appointment.status = "已取消"
        await appointment.save()

        await LogService.add_operation_log(
            operator=operator,
            module="预约服务",
            action="取消预约",
            target_id=appointment.appointment_no,
            detail=f"取消预约 {appointment.customer_name} - {appointment.service_name}",
        )

        return CancelAppointmentResult(
            message="预约已取消，库存已退还",
            rolled_back=rolled_back,
        )

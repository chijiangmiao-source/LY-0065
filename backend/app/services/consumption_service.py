from typing import Optional

from app.models.member_consumption import MemberConsumption
from app.models.operation_log import OperationLog
from app.services.number_service import NumberService


class ConsumptionService:
    @staticmethod
    async def create_consumption_record(
        member_no: Optional[str],
        member_name: Optional[str],
        phone: Optional[str],
        appointment_no: Optional[str],
        service_id: str,
        service_name: str,
        original_price: float,
        discount_rate: float,
        actual_amount: float,
        pay_method: str,
        balance_before: Optional[float],
        balance_after: Optional[float],
        operator: str,
        remark: Optional[str] = None,
    ) -> MemberConsumption:
        consumption = MemberConsumption(
            consumption_no=await NumberService.generate_consumption_no(),
            member_no=member_no,
            member_name=member_name,
            phone=phone,
            appointment_no=appointment_no,
            service_id=service_id,
            service_name=service_name,
            original_price=original_price,
            discount_rate=discount_rate,
            actual_amount=actual_amount,
            pay_method=pay_method,
            balance_before=balance_before,
            balance_after=balance_after,
            operator=operator,
            remark=remark,
        )
        await consumption.insert()
        return consumption

    @staticmethod
    async def delete_consumption_by_appointment(
        appointment_no: str,
    ) -> bool:
        consumption = await MemberConsumption.find_one(
            MemberConsumption.appointment_no == appointment_no
        )
        if consumption:
            await consumption.delete()
            return True
        return False


class LogService:
    @staticmethod
    async def add_operation_log(
        operator: str,
        module: str,
        action: str,
        target_id: Optional[str] = None,
        detail: Optional[str] = None,
    ) -> OperationLog:
        log = OperationLog(
            log_id=await NumberService.generate_log_id(),
            operator=operator,
            module=module,
            action=action,
            target_id=target_id,
            detail=detail,
        )
        await log.insert()
        return log

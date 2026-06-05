from typing import Optional
from app.models.operation_log import OperationLog
from app.services.number_service import NumberService


async def generate_log_id() -> str:
    return await NumberService.generate_log_id()


async def add_operation_log(
    operator: str,
    module: str,
    action: str,
    target_id: Optional[str] = None,
    detail: Optional[str] = None,
) -> OperationLog:
    log = OperationLog(
        log_id=await generate_log_id(),
        operator=operator,
        module=module,
        action=action,
        target_id=target_id,
        detail=detail,
    )
    await log.insert()
    return log

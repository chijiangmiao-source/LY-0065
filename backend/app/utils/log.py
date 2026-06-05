from datetime import datetime
from typing import Optional
from app.models.operation_log import OperationLog


async def generate_log_id() -> str:
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"LOG{today}"
    last_log = await OperationLog.find(OperationLog.log_id.startswith(prefix)).sort("-log_id").first_or_none()
    if last_log:
        seq = int(last_log.log_id[-6:]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:06d}"


async def add_operation_log(
    operator: str,
    module: str,
    action: str,
    target_id: Optional[str] = None,
    detail: Optional[str] = None,
):
    log = OperationLog(
        log_id=await generate_log_id(),
        operator=operator,
        module=module,
        action=action,
        target_id=target_id,
        detail=detail,
    )
    await log.insert()

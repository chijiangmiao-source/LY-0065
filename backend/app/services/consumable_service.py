from datetime import datetime
from typing import List, Optional, Tuple
from dataclasses import dataclass

from app.models.consumable import Consumable
from app.models.usage import Usage
from app.models.service_consumable_template import ServiceConsumableTemplate
from app.services.number_service import NumberService
from app.services.exceptions import InsufficientStockException


@dataclass
class StockCheckItem:
    consumable_no: str
    consumable_name: str
    required: int
    stock: int
    unit: str
    sufficient: bool
    reason: Optional[str] = None


@dataclass
class StockCheckResult:
    has_template: bool
    items: List[StockCheckItem]
    sufficient: bool
    insufficient_items: List[StockCheckItem]


@dataclass
class ConsumableDeductionResult:
    usages: List[Usage]
    updated_consumables: List[Consumable]


class ConsumableService:
    @staticmethod
    async def check_stock(
        service_id: str,
    ) -> StockCheckResult:
        template = await ServiceConsumableTemplate.find_one(
            ServiceConsumableTemplate.service_id == service_id,
            ServiceConsumableTemplate.status == "启用",
        )
        if not template or not template.items:
            return StockCheckResult(
                has_template=False,
                items=[],
                sufficient=True,
                insufficient_items=[],
            )

        items_detail: List[StockCheckItem] = []
        insufficient_items: List[StockCheckItem] = []

        for item in template.items:
            consumable = await Consumable.find_one(
                Consumable.consumable_no == item["consumable_no"]
            )
            if not consumable:
                insufficient = StockCheckItem(
                    consumable_no=item["consumable_no"],
                    consumable_name=item["consumable_name"],
                    required=item["quantity"],
                    stock=0,
                    unit=item.get("unit", "个"),
                    sufficient=False,
                    reason="耗材不存在",
                )
                insufficient_items.append(insufficient)
                items_detail.append(insufficient)
                continue

            stock_item = StockCheckItem(
                consumable_no=item["consumable_no"],
                consumable_name=item["consumable_name"],
                required=item["quantity"],
                stock=consumable.stock_quantity,
                unit=item.get("unit", "个"),
                sufficient=consumable.stock_quantity >= item["quantity"],
            )
            items_detail.append(stock_item)

            if consumable.stock_quantity < item["quantity"]:
                stock_item.reason = (
                    f"库存不足，需要 {item['quantity']} {item.get('unit', '个')}，"
                    f"当前仅有 {consumable.stock_quantity} {item.get('unit', '个')}"
                )
                insufficient_items.append(stock_item)

        return StockCheckResult(
            has_template=True,
            items=items_detail,
            sufficient=len(insufficient_items) == 0,
            insufficient_items=insufficient_items,
        )

    @staticmethod
    async def deduct_consumables_for_service(
        service_id: str,
        appointment_no: str,
        service_name: str,
        employee_id: Optional[str],
        employee_name: Optional[str],
        operator_name: str,
    ) -> ConsumableDeductionResult:
        template = await ServiceConsumableTemplate.find_one(
            ServiceConsumableTemplate.service_id == service_id,
            ServiceConsumableTemplate.status == "启用",
        )
        if not template or not template.items:
            return ConsumableDeductionResult(usages=[], updated_consumables=[])

        insufficient_items = []
        consumables_to_update = []

        for item in template.items:
            consumable = await Consumable.find_one(
                Consumable.consumable_no == item["consumable_no"]
            )
            if not consumable:
                insufficient_items.append(f"{item['consumable_name']}: 耗材不存在")
                continue
            if consumable.stock_quantity < item["quantity"]:
                insufficient_items.append(
                    f"{item['consumable_name']}: 需要 {item['quantity']} {item.get('unit', '个')}，"
                    f"当前库存仅有 {consumable.stock_quantity} {item.get('unit', '个')}"
                )
                continue
            consumables_to_update.append((consumable, item))

        if insufficient_items:
            raise InsufficientStockException(
                "库存不足，无法完成服务，请先补充耗材库存",
                insufficient_items=insufficient_items,
            )

        usages: List[Usage] = []
        updated_consumables: List[Consumable] = []

        for consumable, item in consumables_to_update:
            consumable.stock_quantity -= item["quantity"]
            await consumable.save()
            updated_consumables.append(consumable)

            usage_no = await NumberService.generate_usage_no()
            db_usage = Usage(
                usage_no=usage_no,
                consumable_no=item["consumable_no"],
                consumable_name=item["consumable_name"],
                quantity=item["quantity"],
                employee_id=employee_id or operator_name,
                employee_name=employee_name or operator_name,
                usage_date=datetime.now().strftime("%Y-%m-%d"),
                source_type="自动扣减",
                appointment_no=appointment_no,
                remark=f"服务完成自动扣减: {service_name}",
            )
            await db_usage.insert()
            usages.append(db_usage)

        return ConsumableDeductionResult(
            usages=usages,
            updated_consumables=updated_consumables,
        )

    @staticmethod
    async def rollback_deductions(
        appointment_no: str,
    ) -> Tuple[List[Consumable], int]:
        auto_usages = await Usage.find(
            Usage.appointment_no == appointment_no,
            Usage.source_type == "自动扣减",
        ).to_list()

        restored_consumables: List[Consumable] = []
        for usage in auto_usages:
            consumable = await Consumable.find_one(
                Consumable.consumable_no == usage.consumable_no
            )
            if consumable:
                consumable.stock_quantity += usage.quantity
                await consumable.save()
                restored_consumables.append(consumable)
            await usage.delete()

        return restored_consumables, len(auto_usages)

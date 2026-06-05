import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.models.consumable import Consumable
from app.models.service_consumable_template import ServiceConsumableTemplate
from app.models.usage import Usage

from app.services.exceptions import InsufficientStockException
from app.services.consumable_service import ConsumableService


def _make_consumable(**kwargs):
    defaults = dict(
        consumable_no="C001",
        name="洗发水",
        stock_quantity=50,
        warning_threshold=10,
        unit="瓶",
        status="正常",
    )
    defaults.update(kwargs)
    return Consumable(**defaults)


class TestConsumableService:
    @pytest.mark.asyncio
    async def test_check_stock_no_template(self):
        with patch.object(ServiceConsumableTemplate, "find_one", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = None
            result = await ConsumableService.check_stock("S001")
            assert result.has_template is False
            assert result.sufficient is True
            assert result.items == []

    @pytest.mark.asyncio
    async def test_check_stock_empty_items(self):
        template = ServiceConsumableTemplate(
            template_id="T001", service_id="S001", service_name="洗剪吹", items=[]
        )
        with patch.object(ServiceConsumableTemplate, "find_one", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = template
            result = await ConsumableService.check_stock("S001")
            assert result.has_template is True
            assert result.sufficient is True

    @pytest.mark.asyncio
    async def test_check_stock_consumable_not_found(self):
        template = ServiceConsumableTemplate(
            template_id="T001",
            service_id="S001",
            service_name="洗剪吹",
            items=[{"consumable_no": "C999", "consumable_name": "洗发水", "quantity": 1, "unit": "瓶"}],
        )
        with patch.object(ServiceConsumableTemplate, "find_one", new_callable=AsyncMock) as mock_find_template, \
             patch.object(Consumable, "find_one", new_callable=AsyncMock) as mock_find_consumable:
            mock_find_template.return_value = template
            mock_find_consumable.return_value = None
            result = await ConsumableService.check_stock("S001")
            assert result.sufficient is False
            assert len(result.insufficient_items) == 1
            assert result.insufficient_items[0].reason == "耗材不存在"

    @pytest.mark.asyncio
    async def test_check_stock_insufficient(self):
        template = ServiceConsumableTemplate(
            template_id="T001",
            service_id="S001",
            service_name="洗剪吹",
            items=[{"consumable_no": "C001", "consumable_name": "洗发水", "quantity": 5, "unit": "瓶"}],
        )
        consumable = _make_consumable(stock_quantity=2)
        with patch.object(ServiceConsumableTemplate, "find_one", new_callable=AsyncMock) as mock_find_template, \
             patch.object(Consumable, "find_one", new_callable=AsyncMock) as mock_find_consumable:
            mock_find_template.return_value = template
            mock_find_consumable.return_value = consumable
            result = await ConsumableService.check_stock("S001")
            assert result.sufficient is False
            assert len(result.insufficient_items) == 1
            assert "库存不足" in result.insufficient_items[0].reason

    @pytest.mark.asyncio
    async def test_check_stock_sufficient(self):
        template = ServiceConsumableTemplate(
            template_id="T001",
            service_id="S001",
            service_name="洗剪吹",
            items=[{"consumable_no": "C001", "consumable_name": "洗发水", "quantity": 2, "unit": "瓶"}],
        )
        consumable = _make_consumable(stock_quantity=50)
        with patch.object(ServiceConsumableTemplate, "find_one", new_callable=AsyncMock) as mock_find_template, \
             patch.object(Consumable, "find_one", new_callable=AsyncMock) as mock_find_consumable:
            mock_find_template.return_value = template
            mock_find_consumable.return_value = consumable
            result = await ConsumableService.check_stock("S001")
            assert result.sufficient is True
            assert len(result.insufficient_items) == 0

    @pytest.mark.asyncio
    async def test_deduct_consumables_no_template(self):
        with patch.object(ServiceConsumableTemplate, "find_one", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = None
            result = await ConsumableService.deduct_consumables_for_service(
                service_id="S001",
                appointment_no="A001",
                service_name="洗剪吹",
                employee_id="E001",
                employee_name="李师傅",
                operator_name="admin",
            )
            assert result.usages == []
            assert result.updated_consumables == []

    @pytest.mark.asyncio
    async def test_deduct_consumables_insufficient(self):
        template = ServiceConsumableTemplate(
            template_id="T001",
            service_id="S001",
            service_name="洗剪吹",
            items=[{"consumable_no": "C001", "consumable_name": "洗发水", "quantity": 5, "unit": "瓶"}],
        )
        consumable = _make_consumable(stock_quantity=1)
        with patch.object(ServiceConsumableTemplate, "find_one", new_callable=AsyncMock) as mock_find_template, \
             patch.object(Consumable, "find_one", new_callable=AsyncMock) as mock_find_consumable:
            mock_find_template.return_value = template
            mock_find_consumable.return_value = consumable
            with pytest.raises(InsufficientStockException):
                await ConsumableService.deduct_consumables_for_service(
                    service_id="S001",
                    appointment_no="A001",
                    service_name="洗剪吹",
                    employee_id="E001",
                    employee_name="李师傅",
                    operator_name="admin",
                )

    @pytest.mark.asyncio
    @patch("app.services.consumable_service.NumberService")
    async def test_deduct_consumables_success(self, mock_number):
        template = ServiceConsumableTemplate(
            template_id="T001",
            service_id="S001",
            service_name="洗剪吹",
            items=[{"consumable_no": "C001", "consumable_name": "洗发水", "quantity": 2, "unit": "瓶"}],
        )
        consumable = _make_consumable(stock_quantity=50)
        consumable.save = AsyncMock()
        mock_number.generate_usage_no = AsyncMock(return_value="LY209901010001")

        with patch.object(ServiceConsumableTemplate, "find_one", new_callable=AsyncMock) as mock_find_template, \
             patch.object(Consumable, "find_one", new_callable=AsyncMock) as mock_find_consumable, \
             patch.object(Usage, "insert", new_callable=AsyncMock):
            mock_find_template.return_value = template
            mock_find_consumable.return_value = consumable
            result = await ConsumableService.deduct_consumables_for_service(
                service_id="S001",
                appointment_no="A001",
                service_name="洗剪吹",
                employee_id="E001",
                employee_name="李师傅",
                operator_name="admin",
            )

        assert len(result.usages) == 1
        assert len(result.updated_consumables) == 1
        assert consumable.stock_quantity == 48
        assert result.usages[0].source_type == "自动扣减"
        assert result.usages[0].appointment_no == "A001"

    @pytest.mark.asyncio
    async def test_rollback_deductions(self):
        usage = Usage(
            usage_no="LY001",
            consumable_no="C001",
            consumable_name="洗发水",
            quantity=2,
            employee_id="E001",
            employee_name="李师傅",
            usage_date="2099-01-01",
            source_type="自动扣减",
            appointment_no="A001",
        )
        consumable = _make_consumable(stock_quantity=48)
        consumable.save = AsyncMock()
        usage.delete = AsyncMock()

        mock_find_usages = MagicMock()
        mock_find_usages.to_list = AsyncMock(return_value=[usage])

        with patch.object(Usage, "find", return_value=mock_find_usages), \
             patch.object(Consumable, "find_one", new_callable=AsyncMock) as mock_find_consumable:
            mock_find_consumable.return_value = consumable
            restored, count = await ConsumableService.rollback_deductions("A001")

        assert count == 1
        assert len(restored) == 1
        assert consumable.stock_quantity == 50

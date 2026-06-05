from datetime import datetime

from app.models.usage import Usage
from app.models.member_consumption import MemberConsumption
from app.models.package_redemption import PackageRedemption
from app.models.operation_log import OperationLog
from app.models.member import Member
from app.models.member_recharge import MemberRecharge
from app.models.member_package import MemberPackage
from app.models.package_card import PackageCard
from app.models.member_level import MemberLevel


class NumberService:
    @staticmethod
    async def _generate(prefix_pattern: str, model, field: str, seq_length: int = 4) -> str:
        today = datetime.now().strftime(prefix_pattern)
        prefix = f"{today}"
        last = await model.find({field: {"$regex": f"^{prefix}"}}).sort(f"-{field}").first_or_none()
        if last:
            seq = int(getattr(last, field)[-seq_length:]) + 1
        else:
            seq = 1
        return f"{prefix}{seq:0{seq_length}d}"

    @staticmethod
    async def generate_usage_no() -> str:
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"LY{today}"
        last = await Usage.find(Usage.usage_no.startswith(prefix)).sort("-usage_no").first_or_none()
        if last:
            seq = int(last.usage_no[-4:]) + 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    @staticmethod
    async def generate_consumption_no() -> str:
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"C{today}"
        last = await MemberConsumption.find(MemberConsumption.consumption_no.startswith(prefix)).sort("-consumption_no").first_or_none()
        if last:
            seq = int(last.consumption_no[-4:]) + 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    @staticmethod
    async def generate_redemption_no() -> str:
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"R{today}"
        last = await PackageRedemption.find(PackageRedemption.redemption_no.startswith(prefix)).sort("-redemption_no").first_or_none()
        if last:
            seq = int(last.redemption_no[-4:]) + 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    @staticmethod
    async def generate_log_id() -> str:
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"LOG{today}"
        last = await OperationLog.find(OperationLog.log_id.startswith(prefix)).sort("-log_id").first_or_none()
        if last:
            seq = int(last.log_id[-6:]) + 1
        else:
            seq = 1
        return f"{prefix}{seq:06d}"

    @staticmethod
    async def generate_member_no() -> str:
        today = datetime.now().strftime("%Y%m")
        prefix = f"M{today}"
        last = await Member.find(Member.member_no.startswith(prefix)).sort("-member_no").first_or_none()
        if last:
            seq = int(last.member_no[-4:]) + 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    @staticmethod
    async def generate_recharge_no() -> str:
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"R{today}"
        last = await MemberRecharge.find(MemberRecharge.recharge_no.startswith(prefix)).sort("-recharge_no").first_or_none()
        if last:
            seq = int(last.recharge_no[-4:]) + 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    @staticmethod
    async def generate_member_package_no() -> str:
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"MP{today}"
        last = await MemberPackage.find(MemberPackage.member_package_no.startswith(prefix)).sort("-member_package_no").first_or_none()
        if last:
            seq = int(last.member_package_no[-4:]) + 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    @staticmethod
    async def generate_package_no() -> str:
        today = datetime.now().strftime("%Y%m")
        prefix = f"P{today}"
        last = await PackageCard.find(PackageCard.package_no.startswith(prefix)).sort("-package_no").first_or_none()
        if last:
            seq = int(last.package_no[-4:]) + 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    @staticmethod
    async def generate_level_id() -> str:
        last = await MemberLevel.find_all().sort("-level_id").first_or_none()
        if last:
            seq = int(last.level_id[2:]) + 1
        else:
            seq = 1
        return f"LV{seq:03d}"

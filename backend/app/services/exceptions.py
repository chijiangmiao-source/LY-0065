from typing import Any, Optional


class BusinessException(Exception):
    def __init__(self, message: str, detail: Optional[Any] = None, status_code: int = 400):
        self.message = message
        self.detail = detail
        self.status_code = status_code
        super().__init__(message)


class ValidationException(BusinessException):
    def __init__(self, message: str, detail: Optional[Any] = None):
        super().__init__(message, detail, status_code=400)


class InsufficientBalanceException(BusinessException):
    def __init__(self, message: str, current_balance: Optional[float] = None, required: Optional[float] = None):
        detail = {"current_balance": current_balance, "required": required} if current_balance is not None else None
        super().__init__(message, detail, status_code=400)


class InsufficientStockException(BusinessException):
    def __init__(self, message: str, insufficient_items: Optional[list] = None):
        detail = {"insufficient_items": insufficient_items} if insufficient_items else None
        super().__init__(message, detail, status_code=400)


class PackageInvalidException(BusinessException):
    def __init__(self, message: str, detail: Optional[Any] = None):
        super().__init__(message, detail, status_code=400)

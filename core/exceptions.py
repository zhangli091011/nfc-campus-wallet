"""
统一异常定义 for NFC Campus E-Wallet System.

定义所有业务逻辑异常，便于统一处理和错误响应。
"""


class BusinessException(Exception):
    """业务逻辑异常基类"""
    
    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class UserNotFoundError(BusinessException):
    """用户不存在异常"""
    
    def __init__(self, message: str = None, uid: str = None, error_code: str = "USER_NOT_FOUND"):
        if message is None and uid is not None:
            message = f"User with UID '{uid}' does not exist"
        elif message is None:
            message = "User not found"
        super().__init__(
            message=message,
            error_code=error_code
        )
        self.uid = uid


class ValidationError(BusinessException):
    """验证错误异常"""
    
    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        super().__init__(
            message=message,
            error_code=error_code
        )


class ResourceNotFoundError(BusinessException):
    """资源不存在异常"""
    
    def __init__(self, message: str, error_code: str = "RESOURCE_NOT_FOUND"):
        super().__init__(
            message=message,
            error_code=error_code
        )


class AccountNotFoundError(BusinessException):
    """账户不存在异常"""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="ACCOUNT_NOT_FOUND"
        )


class InsufficientFundsError(BusinessException):
    """余额不足异常"""
    
    def __init__(self, balance: float, amount: float):
        super().__init__(
            message=f"Account balance ({balance}) is insufficient for payment amount ({amount})",
            error_code="INSUFFICIENT_FUNDS"
        )
        self.balance = balance
        self.amount = amount


class InvalidTransactionError(BusinessException):
    """无效交易异常"""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="INVALID_TRANSACTION"
        )


class TransactionNotFoundError(BusinessException):
    """交易不存在异常"""
    
    def __init__(self, transaction_id: int):
        super().__init__(
            message=f"Transaction with ID '{transaction_id}' does not exist",
            error_code="TRANSACTION_NOT_FOUND"
        )
        self.transaction_id = transaction_id


class MerchantNotFoundError(BusinessException):
    """商户不存在异常"""
    
    def __init__(self, merchant_id: str):
        super().__init__(
            message=f"Merchant with ID '{merchant_id}' does not exist",
            error_code="MERCHANT_NOT_FOUND"
        )
        self.merchant_id = merchant_id


class MerchantInactiveError(BusinessException):
    """商户未激活异常"""
    
    def __init__(self, merchant_id: str):
        super().__init__(
            message=f"Merchant '{merchant_id}' is not active",
            error_code="MERCHANT_INACTIVE"
        )
        self.merchant_id = merchant_id


class SignatureError(BusinessException):
    """签名相关异常基类"""
    pass


class TimestampExpiredError(SignatureError):
    """时间戳过期异常"""
    
    def __init__(self, time_diff: float):
        super().__init__(
            message=f"Request timestamp expired. Time difference: {time_diff:.0f} seconds",
            error_code="TIMESTAMP_EXPIRED"
        )
        self.time_diff = time_diff


class TimestampInvalidError(SignatureError):
    """时间戳无效异常（未来时间）"""
    
    def __init__(self, time_diff: float):
        super().__init__(
            message=f"Request timestamp is in the future. Time difference: {abs(time_diff):.0f} seconds",
            error_code="TIMESTAMP_INVALID"
        )
        self.time_diff = time_diff


class SignatureVerificationError(SignatureError):
    """签名验证失败异常"""
    
    def __init__(self):
        super().__init__(
            message="Signature verification failed",
            error_code="SIGNATURE_INVALID"
        )


class BusinessLogicError(BusinessException):
    """业务逻辑错误异常"""
    
    def __init__(self, message: str, error_code: str = "BUSINESS_LOGIC_ERROR"):
        super().__init__(
            message=message,
            error_code=error_code
        )

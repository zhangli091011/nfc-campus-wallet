"""
Structured logging utility for NFC Campus E-Wallet System.

Provides JSON-formatted logging for machine parsing and monitoring.
All log entries include timestamp, level, and structured data fields.
"""

import logging
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from decimal import Decimal


class StructuredLogger:
    """
    Structured logger that outputs JSON-formatted log entries.
    
    Provides methods for logging API requests, authentication failures,
    database errors, and balance modifications in a consistent format.
    """
    
    def __init__(self, logger_name: str):
        """
        Initialize structured logger.
        
        Args:
            logger_name: Name of the logger (typically module name)
        """
        self.logger = logging.getLogger(logger_name)
    
    def _log_json(self, level: int, event_type: str, data: Dict[str, Any]):
        """
        Log structured data as JSON.
        
        Args:
            level: Logging level (logging.INFO, logging.WARNING, etc.)
            event_type: Type of event being logged
            data: Dictionary of structured data to log
        """
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            **data
        }
        
        # Convert Decimal to float for JSON serialization
        for key, value in log_entry.items():
            if isinstance(value, Decimal):
                log_entry[key] = float(value)
        
        self.logger.log(level, json.dumps(log_entry))
    
    def log_api_request(
        self,
        endpoint: str,
        method: str,
        uid: Optional[str] = None,
        status_code: int = 200,
        result: str = "success",
        error_code: Optional[str] = None,
        duration_ms: Optional[float] = None
    ):
        """
        Log API request with result status.
        
        Args:
            endpoint: API endpoint path (e.g., "/balance", "/pay")
            method: HTTP method (GET, POST, etc.)
            uid: User identifier (if applicable)
            status_code: HTTP status code
            result: Result status ("success" or "error")
            error_code: Error code if request failed
            duration_ms: Request duration in milliseconds
        """
        data = {
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "result": result
        }
        
        if uid:
            data["uid"] = uid
        if error_code:
            data["error_code"] = error_code
        if duration_ms is not None:
            data["duration_ms"] = duration_ms
        
        level = logging.INFO if result == "success" else logging.WARNING
        self._log_json(level, "api_request", data)
    
    def log_authentication_failure(
        self,
        endpoint: str,
        reason: str,
        uid: Optional[str] = None,
        timestamp: Optional[int] = None,
        error_code: str = "AUTH_ERROR"
    ):
        """
        Log authentication failure with reason.
        
        Args:
            endpoint: API endpoint path
            reason: Reason for authentication failure
            uid: User identifier (if available)
            timestamp: Request timestamp (if available)
            error_code: Specific error code
        """
        data = {
            "endpoint": endpoint,
            "reason": reason,
            "error_code": error_code
        }
        
        if uid:
            data["uid"] = uid
        if timestamp is not None:
            data["request_timestamp"] = timestamp
        
        self._log_json(logging.WARNING, "authentication_failure", data)
    
    def log_database_error(
        self,
        operation: str,
        error_type: str,
        error_message: str,
        uid: Optional[str] = None,
        transaction_id: Optional[int] = None
    ):
        """
        Log database transaction failure with error details.
        
        Args:
            operation: Database operation being performed (e.g., "payment", "recharge")
            error_type: Type of error (e.g., "IntegrityError", "OperationalError")
            error_message: Detailed error message
            uid: User identifier (if applicable)
            transaction_id: Transaction ID (if applicable)
        """
        data = {
            "operation": operation,
            "error_type": error_type,
            "error_message": error_message
        }
        
        if uid:
            data["uid"] = uid
        if transaction_id is not None:
            data["transaction_id"] = transaction_id
        
        self._log_json(logging.ERROR, "database_error", data)
    
    def log_balance_modification(
        self,
        uid: str,
        transaction_type: str,
        amount: Decimal,
        old_balance: Decimal,
        new_balance: Decimal,
        transaction_id: Optional[int] = None,
        merchant_id: Optional[str] = None
    ):
        """
        Log balance modification with old/new balance and transaction type.
        
        Args:
            uid: User identifier
            transaction_type: Type of transaction ("payment" or "recharge")
            amount: Transaction amount
            old_balance: Balance before transaction
            new_balance: Balance after transaction
            transaction_id: Transaction record ID
            merchant_id: Merchant identifier (for payments)
        """
        data = {
            "uid": uid,
            "transaction_type": transaction_type,
            "amount": float(amount),
            "old_balance": float(old_balance),
            "new_balance": float(new_balance)
        }
        
        if transaction_id is not None:
            data["transaction_id"] = transaction_id
        if merchant_id:
            data["merchant_id"] = merchant_id
        
        self._log_json(logging.INFO, "balance_modification", data)
    
    def log_validation_error(
        self,
        endpoint: str,
        field: str,
        value: Any,
        reason: str,
        uid: Optional[str] = None
    ):
        """
        Log input validation error.
        
        Args:
            endpoint: API endpoint path
            field: Field that failed validation
            value: Invalid value
            reason: Reason for validation failure
            uid: User identifier (if applicable)
        """
        data = {
            "endpoint": endpoint,
            "field": field,
            "value": str(value),
            "reason": reason
        }
        
        if uid:
            data["uid"] = uid
        
        self._log_json(logging.WARNING, "validation_error", data)
    
    def log_business_logic_error(
        self,
        operation: str,
        error_code: str,
        message: str,
        uid: Optional[str] = None,
        **kwargs
    ):
        """
        Log business logic error (e.g., insufficient funds, user not found).
        
        Args:
            operation: Operation being performed
            error_code: Error code
            message: Error message
            uid: User identifier (if applicable)
            **kwargs: Additional context data
        """
        data = {
            "operation": operation,
            "error_code": error_code,
            "message": message,
            **kwargs
        }
        
        if uid:
            data["uid"] = uid
        
        self._log_json(logging.WARNING, "business_logic_error", data)


def get_structured_logger(logger_name: str) -> StructuredLogger:
    """
    Get a structured logger instance.
    
    Args:
        logger_name: Name of the logger (typically __name__)
    
    Returns:
        StructuredLogger: Configured structured logger instance
    """
    return StructuredLogger(logger_name)

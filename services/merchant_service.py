"""
Merchant service for NFC Campus E-Wallet System.

Manages merchant validation operations.
"""

from sqlalchemy.orm import Session
import logging

from models.merchant import Merchant
from core.exceptions import MerchantNotFoundError, MerchantInactiveError
from utils.structured_logger import get_structured_logger

logger = logging.getLogger(__name__)
structured_logger = get_structured_logger(__name__)


# 移除旧的异常定义，使用 core.exceptions 中的


class MerchantService:
    """
    Service class for merchant operations.
    
    Provides methods to validate merchants for payment processing.
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize MerchantService with database session.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session
    
    def validate_merchant(self, merchant_id: str) -> Merchant:
        """
        Validate that a merchant exists and is active.
        
        This method checks:
        1. The merchant_id exists in the merchants table
        2. The merchant's is_active flag is True
        
        Args:
            merchant_id: Unique merchant identifier
            
        Returns:
            Merchant: The validated merchant record
            
        Raises:
            MerchantNotFoundError: If merchant with specified merchant_id does not exist
            MerchantInactiveError: If merchant exists but is_active is False
            
        Example:
            >>> service = MerchantService(db_session)
            >>> merchant = service.validate_merchant("MERCHANT001")
            >>> print(merchant.name)
            'Campus Cafeteria'
        """
        try:
            # Query merchant by merchant_id
            merchant = self.db.query(Merchant).filter(
                Merchant.merchant_id == merchant_id
            ).first()
            
            # Check if merchant exists
            if merchant is None:
                logger.warning(f"Merchant validation failed: Merchant {merchant_id} not found")
                structured_logger.log_business_logic_error(
                    operation="merchant_validation",
                    error_code="MERCHANT_NOT_FOUND",
                    message=f"Merchant with ID '{merchant_id}' does not exist",
                    merchant_id=merchant_id
                )
                raise MerchantNotFoundError(
                    f"Merchant with ID '{merchant_id}' does not exist"
                )
            
            # Check if merchant is active
            if not merchant.is_active:
                logger.warning(
                    f"Merchant validation failed: Merchant {merchant_id} is inactive"
                )
                structured_logger.log_business_logic_error(
                    operation="merchant_validation",
                    error_code="MERCHANT_INACTIVE",
                    message=f"Merchant '{merchant.name}' (ID: {merchant_id}) is not active",
                    merchant_id=merchant_id
                )
                raise MerchantInactiveError(
                    f"Merchant '{merchant.name}' (ID: {merchant_id}) is not active"
                )
            
            logger.info(f"Merchant validation successful: {merchant_id} - {merchant.name}")
            return merchant
            
        except (MerchantNotFoundError, MerchantInactiveError):
            # Re-raise business logic errors
            raise
        except Exception as e:
            logger.error(f"Unexpected error validating merchant {merchant_id}: {e}")
            structured_logger.log_database_error(
                operation="merchant_validation",
                error_type=type(e).__name__,
                error_message=str(e)
            )
            raise
    
    def merchant_exists(self, merchant_id: str) -> bool:
        """
        Check if a merchant exists in the database.
        
        Args:
            merchant_id: Unique merchant identifier
            
        Returns:
            bool: True if merchant exists, False otherwise
            
        Example:
            >>> service = MerchantService(db_session)
            >>> service.merchant_exists("MERCHANT001")
            True
        """
        try:
            count = self.db.query(Merchant).filter(
                Merchant.merchant_id == merchant_id
            ).count()
            return count > 0
        except Exception as e:
            logger.error(f"Error checking merchant existence for {merchant_id}: {e}")
            raise

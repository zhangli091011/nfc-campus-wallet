"""
Ledger Service for NFC Campus E-Wallet System.

账本服务：实现账本追加模式的核心逻辑�?
所有余额变更必须通过此服务进行，确保账本一致性和可审计性�?
"""

from sqlalchemy.orm import Session
from typing import Optional, Tuple
import logging

from models.user import User
from models.account import Account
from models.transaction import Transaction, TransactionType
from core.exceptions import (
    InsufficientFundsError,
    UserNotFoundError,
    InvalidTransactionError,
    AccountNotFoundError
)

logger = logging.getLogger(__name__)


class LedgerEntry:
    """
    账本条目结果�?
    
    Attributes:
        transaction_id: 交易ID
        balance_before: 交易前余额（分）
        balance_after: 交易后余额（分）
        amount: 交易金额（分�?
    """
    
    def __init__(
        self,
        transaction_id: int,
        balance_before: int,
        balance_after: int,
        amount: int
    ):
        self.transaction_id = transaction_id
        self.balance_before = balance_before
        self.balance_after = balance_after
        self.amount = amount
    
    @property
    def balance_before_yuan(self) -> float:
        """交易前余额（元）- 值已为元"""
        return float(self.balance_before)
    
    @property
    def balance_after_yuan(self) -> float:
        """交易后余额（元）- 值已为元"""
        return float(self.balance_after)
    
    @property
    def amount_yuan(self) -> float:
        """交易金额（元�? 值已为元"""
        return float(self.amount)


class LedgerService:
    """
    账本服务类�?
    
    实现账本追加模式的核心功能：
    1. 所有交易都是追加记录，不可修改
    2. 每条记录包含交易前后余额
    3. 使用行锁（SELECT ... FOR UPDATE）保证并发安�?
    4. 事务边界：每次操作都在数据库事务内完�?
    """
    
    def __init__(self, db_session: Session):
        """
        初始化账本服务�?
        
        Args:
            db_session: SQLAlchemy 数据库会�?
        """
        self.db = db_session
    
    def _yuan_to_cents(self, yuan: float) -> int:
        """
        将元转换为分�?
        
        Args:
            yuan: 金额（元�?
            
        Returns:
            金额（分�?
        """
        return int(round(yuan * 100))
    
    def _acquire_user_lock(self, uid: str) -> User:
        """
        获取用户行锁�?
        
        使用 SELECT ... FOR UPDATE 锁定用户记录，防止并发修改�?
        
        Args:
            uid: 用户UID
            
        Returns:
            User: 用户对象
            
        Raises:
            UserNotFoundError: 用户不存�?
        """
        user = self.db.query(User).filter(User.uid == uid).with_for_update().first()
        
        if user is None:
            logger.warning(f"User not found: {uid}")
            raise UserNotFoundError(f"User with UID '{uid}' does not exist")
        
        return user
    
    def _acquire_account_lock(self, account_id: int) -> Account:
        """
        获取账户行锁�?
        
        使用 SELECT ... FOR UPDATE 锁定账户记录，防止并发修改�?
        
        Args:
            account_id: 账户ID
            
        Returns:
            Account: 账户对象
            
        Raises:
            AccountNotFoundError: 账户不存�?
        """
        account = self.db.query(Account).filter(
            Account.id == account_id
        ).with_for_update().first()
        
        if account is None:
            logger.warning(f"Account not found: {account_id}")
            raise AccountNotFoundError(
                f"Account with ID '{account_id}' does not exist"
            )
        
        return account
    
    def _create_ledger_entry(
        self,
        uid: str,
        transaction_type: str,
        amount_cents: int,
        balance_before: int,
        balance_after: int,
        merchant_id: Optional[str] = None,
        related_txn_id: Optional[int] = None,
        remark: Optional[str] = None,
        operator_id: Optional[str] = None
    ) -> Transaction:
        """
        创建账本条目�?
        
        Args:
            uid: 用户UID
            transaction_type: 交易类型
            amount_cents: 交易金额（分�?
            balance_before: 交易前余额（分）
            balance_after: 交易后余额（分）
            merchant_id: 商户ID（可选）
            related_txn_id: 关联交易ID（可选）
            remark: 备注（可选）
            operator_id: 操作员ID（可选）
            
        Returns:
            Transaction: 交易记录
        """
        transaction = Transaction(
            uid=uid,
            card_uid=uid,  # �?uid 保持一�?
            type=transaction_type,
            amount=amount_cents,
            balance_before=balance_before,
            balance_after=balance_after,
            merchant_id=merchant_id,
            related_txn_id=related_txn_id,
            remark=remark,
            operator_id=operator_id
        )
        
        self.db.add(transaction)
        return transaction
    
    def append_credit(
        self,
        uid: str,
        amount_yuan: float,
        transaction_type: str = "recharge",
        merchant_id: Optional[str] = None,
        related_txn_id: Optional[int] = None,
        remark: Optional[str] = None,
        operator_id: Optional[str] = None
    ) -> LedgerEntry:
        """
        追加贷方记录（增加余额）�?
        
        适用于：recharge（充值）、refund（退款）、adjust（调�?增加�?
        
        Args:
            uid: 用户UID
            amount_yuan: 金额（元�?
            transaction_type: 交易类型
            merchant_id: 商户ID（可选）
            related_txn_id: 关联交易ID（可选）
            remark: 备注（可选）
            operator_id: 操作员ID（可选）
            
        Returns:
            LedgerEntry: 账本条目结果
            
        Raises:
            UserNotFoundError: 用户不存�?
            InvalidTransactionError: 交易类型不正�?
        """
        # 验证交易类型
        if transaction_type not in ["recharge", "refund", "adjust", "issue"]:
            raise InvalidTransactionError(
                f"Invalid credit transaction type: {transaction_type}"
            )
        
        try:
            # 转换金额为分
            amount_cents = self._yuan_to_cents(amount_yuan)
            
            if amount_cents <= 0:
                raise InvalidTransactionError("Amount must be positive")
            
            # 获取用户行锁
            user = self._acquire_user_lock(uid)
            
            # 记录交易前余�?
            balance_before = user.balance
            
            # 计算交易后余�?
            balance_after = balance_before + amount_cents
            
            # 更新用户余额
            user.balance = balance_after
            
            # 创建账本条目
            transaction = self._create_ledger_entry(
                uid=uid,
                transaction_type=transaction_type,
                amount_cents=amount_cents,
                balance_before=balance_before,
                balance_after=balance_after,
                merchant_id=merchant_id,
                related_txn_id=related_txn_id,
                remark=remark,
                operator_id=operator_id
            )
            
            # 提交事务
            self.db.commit()
            
            # 刷新获取交易ID
            self.db.refresh(transaction)
            
            logger.info(
                f"Credit transaction successful: uid={uid}, type={transaction_type}, "
                f"amount={amount_cents} cents, balance_before={balance_before}, "
                f"balance_after={balance_after}, txn_id={transaction.id}"
            )
            
            return LedgerEntry(
                transaction_id=transaction.id,
                balance_before=balance_before,
                balance_after=balance_after,
                amount=amount_cents
            )
            
        except (UserNotFoundError, InvalidTransactionError):
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(
                f"Credit transaction failed: uid={uid}, type={transaction_type}, "
                f"amount={amount_yuan}, error={str(e)}",
                exc_info=True
            )
            raise
    
    def append_debit(
        self,
        uid: str,
        amount_yuan: float,
        transaction_type: str = "pay",
        merchant_id: Optional[str] = None,
        related_txn_id: Optional[int] = None,
        remark: Optional[str] = None,
        operator_id: Optional[str] = None
    ) -> LedgerEntry:
        """
        追加借方记录（减少余额）�?
        
        适用于：pay（支付）、void（作废）、expire（过期）、adjust（调�?减少�?
        
        Args:
            uid: 用户UID
            amount_yuan: 金额（元�?
            transaction_type: 交易类型
            merchant_id: 商户ID（可选）
            related_txn_id: 关联交易ID（可选）
            remark: 备注（可选）
            operator_id: 操作员ID（可选）
            
        Returns:
            LedgerEntry: 账本条目结果
            
        Raises:
            UserNotFoundError: 用户不存�?
            InsufficientFundsError: 余额不足
            InvalidTransactionError: 交易类型不正�?
        """
        # 验证交易类型
        if transaction_type not in ["pay", "void", "expire", "adjust"]:
            raise InvalidTransactionError(
                f"Invalid debit transaction type: {transaction_type}"
            )
        
        try:
            # 转换金额为分
            amount_cents = self._yuan_to_cents(amount_yuan)
            
            if amount_cents <= 0:
                raise InvalidTransactionError("Amount must be positive")
            
            # 获取用户行锁
            user = self._acquire_user_lock(uid)
            
            # 记录交易前余�?
            balance_before = user.balance
            
            # 验证余额是否充足
            if balance_before < amount_cents:
                logger.warning(
                    f"Insufficient funds: uid={uid}, balance={balance_before}, "
                    f"required={amount_cents}"
                )
                raise InsufficientFundsError(
                    f"Account balance ({balance_before:.2f} yuan) is insufficient "
                    f"for transaction amount ({amount_yuan:.2f} yuan)"
                )
            
            # 计算交易后余�?
            balance_after = balance_before - amount_cents
            
            # 更新用户余额
            user.balance = balance_after
            
            # 创建账本条目
            transaction = self._create_ledger_entry(
                uid=uid,
                transaction_type=transaction_type,
                amount_cents=amount_cents,
                balance_before=balance_before,
                balance_after=balance_after,
                merchant_id=merchant_id,
                related_txn_id=related_txn_id,
                remark=remark,
                operator_id=operator_id
            )
            
            # 提交事务
            self.db.commit()
            
            # 刷新获取交易ID
            self.db.refresh(transaction)
            
            logger.info(
                f"Debit transaction successful: uid={uid}, type={transaction_type}, "
                f"amount={amount_cents} cents, balance_before={balance_before}, "
                f"balance_after={balance_after}, txn_id={transaction.id}"
            )
            
            return LedgerEntry(
                transaction_id=transaction.id,
                balance_before=balance_before,
                balance_after=balance_after,
                amount=amount_cents
            )
            
        except (UserNotFoundError, InsufficientFundsError, InvalidTransactionError):
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(
                f"Debit transaction failed: uid={uid}, type={transaction_type}, "
                f"amount={amount_yuan}, error={str(e)}",
                exc_info=True
            )
            raise
    
    def append_credit_to_account(
        self,
        account_id: int,
        amount_yuan: float,
        transaction_type: str = "recharge",
        event_id: Optional[int] = None,
        participant_id: Optional[int] = None,
        merchant_id: Optional[str] = None,
        related_txn_id: Optional[int] = None,
        remark: Optional[str] = None,
        operator_id: Optional[str] = None
    ) -> LedgerEntry:
        """
        追加贷方记录到账户（增加余额）�?
        
        适用于：recharge（充值）、refund（退款）、adjust（调�?增加）、loan_issue（发放垫资）
        
        Args:
            account_id: 账户ID
            amount_yuan: 金额（元�?
            transaction_type: 交易类型
            event_id: 活动ID（可选）
            participant_id: 参与者ID（可选）
            merchant_id: 商户ID（可选）
            related_txn_id: 关联交易ID（可选）
            remark: 备注（可选）
            operator_id: 操作员ID（可选）
            
        Returns:
            LedgerEntry: 账本条目结果
            
        Raises:
            AccountNotFoundError: 账户不存�?
            InvalidTransactionError: 交易类型不正�?
        """
        # 验证交易类型
        if transaction_type not in ["recharge", "refund", "adjust", "issue", "loan_issue"]:
            raise InvalidTransactionError(
                f"Invalid credit transaction type: {transaction_type}"
            )
        
        try:
            # 转换金额为分
            amount_cents = self._yuan_to_cents(amount_yuan)
            
            if amount_cents <= 0:
                raise InvalidTransactionError("Amount must be positive")
            
            # 获取账户行锁
            account = self._acquire_account_lock(account_id)
            
            # 记录交易前余�?
            balance_before = account.balance
            
            # 计算交易后余�?
            balance_after = balance_before + amount_cents
            
            # 更新账户余额
            account.balance = balance_after
            
            # 创建账本条目
            transaction = Transaction(
                uid=None,  # 活动模式不使�?uid
                card_uid=account.participant.card_uid if account.participant else None,
                event_id=event_id,
                participant_id=participant_id,
                account_id=account_id,
                type=transaction_type,
                amount=amount_cents,
                balance_before=balance_before,
                balance_after=balance_after,
                merchant_id=merchant_id,
                related_txn_id=related_txn_id,
                remark=remark,
                operator_id=operator_id
            )
            
            self.db.add(transaction)
            
            # 提交事务
            self.db.commit()
            
            # 刷新获取交易ID
            self.db.refresh(transaction)
            
            logger.info(
                f"Credit transaction to account successful: account_id={account_id}, "
                f"type={transaction_type}, amount={amount_cents} cents, "
                f"balance_before={balance_before}, balance_after={balance_after}, "
                f"txn_id={transaction.id}"
            )
            
            return LedgerEntry(
                transaction_id=transaction.id,
                balance_before=balance_before,
                balance_after=balance_after,
                amount=amount_cents
            )
            
        except (AccountNotFoundError, InvalidTransactionError):
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(
                f"Credit transaction to account failed: account_id={account_id}, "
                f"type={transaction_type}, amount={amount_yuan}, error={str(e)}",
                exc_info=True
            )
            raise
    
    def append_debit_from_account(
        self,
        account_id: int,
        amount_yuan: float,
        transaction_type: str = "pay",
        event_id: Optional[int] = None,
        participant_id: Optional[int] = None,
        merchant_id: Optional[str] = None,
        related_txn_id: Optional[int] = None,
        remark: Optional[str] = None,
        operator_id: Optional[int] = None,
        booth_id: Optional[int] = None,
        product_id: Optional[int] = None
    ) -> LedgerEntry:
        """
        追加借方记录从账户（减少余额）�?
        
        适用于：pay（支付）、void（作废）、expire（过期）、adjust（调�?减少）、loan_fee（扣除手续费�?
        
        Args:
            account_id: 账户ID
            amount_yuan: 金额（元�?
            transaction_type: 交易类型
            event_id: 活动ID（可选）
            participant_id: 参与者ID（可选）
            merchant_id: 商户ID（可选）
            related_txn_id: 关联交易ID（可选）
            remark: 备注（可选）
            operator_id: 操作员用户ID（可选，整数�?
            booth_id: 摊位ID（可选，用于摊位管理系统�?
            product_id: 商品ID（可选，用于摊位管理系统�?
            
        Returns:
            LedgerEntry: 账本条目结果
            
        Raises:
            AccountNotFoundError: 账户不存�?
            InsufficientFundsError: 余额不足
            InvalidTransactionError: 交易类型不正�?
        """
        # 验证交易类型
        if transaction_type not in ["pay", "void", "expire", "adjust", "loan_fee"]:
            raise InvalidTransactionError(
                f"Invalid debit transaction type: {transaction_type}"
            )
        
        try:
            # 转换金额为分
            amount_cents = self._yuan_to_cents(amount_yuan)
            
            if amount_cents <= 0:
                raise InvalidTransactionError("Amount must be positive")
            
            # 获取账户行锁
            account = self._acquire_account_lock(account_id)
            
            # 记录交易前余�?
            balance_before = account.balance
            
            # 验证余额是否充足
            if balance_before < amount_cents:
                logger.warning(
                    f"Insufficient funds: account_id={account_id}, "
                    f"balance={balance_before}, required={amount_cents}"
                )
                raise InsufficientFundsError(
                    f"Account balance ({balance_before:.2f} yuan) is insufficient "
                    f"for transaction amount ({amount_yuan:.2f} yuan)"
                )
            
            # 计算交易后余�?
            balance_after = balance_before - amount_cents
            
            # 更新账户余额
            account.balance = balance_after
            
            # 创建账本条目
            transaction = Transaction(
                uid=None,  # 活动模式不使�?uid
                card_uid=account.participant.card_uid if account.participant else None,
                event_id=event_id,
                participant_id=participant_id,
                account_id=account_id,
                type=transaction_type,
                amount=amount_cents,
                balance_before=balance_before,
                balance_after=balance_after,
                merchant_id=merchant_id,
                related_txn_id=related_txn_id,
                remark=remark,
                operator_id=operator_id,
                booth_id=booth_id,
                product_id=product_id
            )
            
            self.db.add(transaction)
            
            # 提交事务
            self.db.commit()
            
            # 刷新获取交易ID
            self.db.refresh(transaction)
            
            logger.info(
                f"Debit transaction from account successful: account_id={account_id}, "
                f"type={transaction_type}, amount={amount_cents} cents, "
                f"balance_before={balance_before}, balance_after={balance_after}, "
                f"booth_id={booth_id}, product_id={product_id}, operator_id={operator_id}, "
                f"txn_id={transaction.id}"
            )
            
            return LedgerEntry(
                transaction_id=transaction.id,
                balance_before=balance_before,
                balance_after=balance_after,
                amount=amount_cents
            )
            
        except (AccountNotFoundError, InsufficientFundsError, InvalidTransactionError):
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(
                f"Debit transaction from account failed: account_id={account_id}, "
                f"type={transaction_type}, amount={amount_yuan}, error={str(e)}",
                exc_info=True
            )
            raise
    
    def verify_balance_integrity(self, uid: str) -> Tuple[bool, str]:
        """
        验证账本完整性�?
        
        检查用户的所有交易记录，验证余额计算是否正确�?
        
        Args:
            uid: 用户UID
            
        Returns:
            Tuple[bool, str]: (是否完整, 错误信息)
        """
        try:
            user = self.db.query(User).filter(User.uid == uid).first()
            if user is None:
                return False, f"User {uid} not found"
            
            # 获取所有交易记录，按时间排�?
            transactions = (
                self.db.query(Transaction)
                .filter(Transaction.uid == uid)
                .order_by(Transaction.created_at, Transaction.id)
                .all()
            )
            
            if not transactions:
                # 没有交易记录，余额应该为0
                if user.balance == 0:
                    return True, "No transactions, balance is correct"
                else:
                    return False, f"No transactions but balance is {user.balance}"
            
            # 验证每条交易的余额计�?
            for i, txn in enumerate(transactions):
                # 验证 balance_before �?balance_after 的关�?
                if txn.type in ["recharge", "refund", "issue"]:
                    expected_after = txn.balance_before + txn.amount
                elif txn.type in ["pay", "void", "expire"]:
                    expected_after = txn.balance_before - txn.amount
                else:  # adjust
                    # adjust 可能是增加或减少，需要根据实际情况判�?
                    expected_after = txn.balance_after
                
                if txn.balance_after != expected_after and txn.type != "adjust":
                    return False, (
                        f"Transaction {txn.id} balance mismatch: "
                        f"expected {expected_after}, got {txn.balance_after}"
                    )
                
                # 验证相邻交易的余额连续�?
                if i > 0:
                    prev_txn = transactions[i - 1]
                    if txn.balance_before != prev_txn.balance_after:
                        return False, (
                            f"Balance discontinuity between transaction {prev_txn.id} "
                            f"and {txn.id}: {prev_txn.balance_after} != {txn.balance_before}"
                        )
            
            # 验证最后一条交易的余额与用户当前余额一�?
            last_txn = transactions[-1]
            if last_txn.balance_after != user.balance:
                return False, (
                    f"Final balance mismatch: last transaction shows {last_txn.balance_after}, "
                    f"but user balance is {user.balance}"
                )
            
            return True, "Balance integrity verified"
            
        except Exception as e:
            logger.error(f"Balance integrity check failed: {str(e)}", exc_info=True)
            return False, f"Error during verification: {str(e)}"

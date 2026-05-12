"""
Transaction service for NFC Campus E-Wallet System (Ledger Mode).

管理支付和充值操作，使用 LedgerService 实现账本追加模式。
"""

from sqlalchemy.orm import Session
from typing import Optional, List, Dict
import logging

from models.user import User
from models.transaction import Transaction
from models.booth import Booth
from models.product import Product
from services.ledger_service import LedgerService, LedgerEntry
from core.exceptions import (
    InsufficientFundsError,
    UserNotFoundError,
    ValidationError,
    ResourceNotFoundError
)

logger = logging.getLogger(__name__)


class TransactionResult:
    """
    交易操作结果。
    
    Attributes:
        success: 交易是否成功
        new_balance: 交易后余额（元）
        transaction_id: 交易记录ID
        balance_before: 交易前余额（元，可选）
    """
    
    def __init__(
        self,
        success: bool,
        new_balance,
        transaction_id: Optional[int] = None,
        balance_before=None
    ):
        self.success = success
        self.new_balance = new_balance
        self.transaction_id = transaction_id
        self.balance_before = balance_before
    
    @property
    def new_balance_yuan(self) -> float:
        """交易后余额（元）"""
        return float(self.new_balance)
    
    @property
    def balance_before_yuan(self) -> Optional[float]:
        """交易前余额（元）"""
        if self.balance_before is not None:
            return float(self.balance_before)
        return None


class TransactionService:
    """
    交易服务类（账本模式）。
    
    提供支付、充值等交易操作，内部使用 LedgerService 实现账本追加模式。
    所有交易都保证 ACID 特性和并发安全。
    """
    
    def __init__(self, db_session: Session):
        """
        初始化交易服务。
        
        Args:
            db_session: SQLAlchemy 数据库会话
        """
        self.db = db_session
        self.ledger_service = LedgerService(db_session)
    
    def process_payment(
        self,
        uid: str,
        amount_yuan: float,
        merchant_id: Optional[str] = None,
        remark: Optional[str] = None
    ) -> TransactionResult:
        """
        处理支付交易。
        
        使用 LedgerService 的 append_debit 方法，保证：
        - 原子性：余额更新和交易记录在同一事务内
        - 一致性：余额验证确保非负
        - 隔离性：SELECT...FOR UPDATE 防止并发修改
        - 持久性：事务提交后数据持久化
        
        Args:
            uid: 用户UID
            amount_yuan: 支付金额（元）
            merchant_id: 商户ID（可选）
            remark: 备注（可选）
            
        Returns:
            TransactionResult: 交易结果
            
        Raises:
            UserNotFoundError: 用户不存在
            InsufficientFundsError: 余额不足
        """
        try:
            # 使用账本服务追加借方记录
            ledger_entry = self.ledger_service.append_debit(
                uid=uid,
                amount_yuan=amount_yuan,
                transaction_type="pay",
                merchant_id=merchant_id,
                remark=remark
            )
            
            logger.info(
                f"Payment successful: uid={uid}, amount={amount_yuan} yuan, "
                f"txn_id={ledger_entry.transaction_id}, "
                f"balance: {ledger_entry.balance_before} -> {ledger_entry.balance_after} yuan"
            )
            
            return TransactionResult(
                success=True,
                new_balance=ledger_entry.balance_after,
                transaction_id=ledger_entry.transaction_id,
                balance_before=ledger_entry.balance_before
            )
            
        except (UserNotFoundError, InsufficientFundsError) as e:
            logger.warning(f"Payment failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Payment transaction failed: {str(e)}", exc_info=True)
            raise
    
    def process_recharge(
        self,
        uid: str,
        amount_yuan: float,
        operator_id: Optional[str] = None,
        remark: Optional[str] = None
    ) -> TransactionResult:
        """
        处理充值交易。
        
        使用 LedgerService 的 append_credit 方法，保证：
        - 原子性：余额更新和交易记录在同一事务内
        - 一致性：余额增加正确
        - 隔离性：SELECT...FOR UPDATE 防止并发修改
        - 持久性：事务提交后数据持久化
        - 是  zhanhgli091011@126.com
        Args:
            uid: 用户UID
            amount_yuan: 充值金额（元）
            operator_id: 操作员ID（可选）
            remark: 备注（可选）
            
        Returns:
            TransactionResult: 交易结果
            
        Raises:
            UserNotFoundError: 用户不存在
        """
        try:
            # 使用账本服务追加贷方记录
            ledger_entry = self.ledger_service.append_credit(
                uid=uid,
                amount_yuan=amount_yuan,
                transaction_type="recharge",
                operator_id=operator_id,
                remark=remark
            )
            
            logger.info(
                f"Recharge successful: uid={uid}, amount={amount_yuan} yuan, "
                f"txn_id={ledger_entry.transaction_id}, "
                f"balance: {ledger_entry.balance_before} -> {ledger_entry.balance_after} yuan"
            )
            
            return TransactionResult(
                success=True,
                new_balance=ledger_entry.balance_after,
                transaction_id=ledger_entry.transaction_id,
                balance_before=ledger_entry.balance_before
            )
            
        except UserNotFoundError as e:
            logger.warning(f"Recharge failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Recharge transaction failed: {str(e)}", exc_info=True)
            raise
    
    def get_transaction_history(
        self,
        uid: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict:
        """
        获取交易历史记录。
        
        Args:
            uid: 用户UID
            start_date: 开始日期（ISO格式，可选）
            end_date: 结束日期（ISO格式，可选）
            limit: 返回记录数限制
            offset: 偏移量
            
        Returns:
            Dict: 包含交易列表和总数
            
        Raises:
            UserNotFoundError: 用户不存在
        """
        try:
            # 验证用户存在
            user = self.db.query(User).filter(User.uid == uid).first()
            if user is None:
                logger.warning(f"Transaction history query failed: User {uid} not found")
                raise UserNotFoundError(f"User with UID '{uid}' does not exist")
            
            # 构建查询
            query = self.db.query(Transaction).filter(Transaction.uid == uid)
            
            # 应用日期过滤
            if start_date:
                from datetime import datetime
                start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(Transaction.created_at >= start_datetime)
            
            if end_date:
                from datetime import datetime
                end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.filter(Transaction.created_at <= end_datetime)
            
            # 获取总数
            total_count = query.count()
            
            # 排序并分页
            query = query.order_by(Transaction.created_at.desc(), Transaction.id.desc())
            query = query.limit(limit).offset(offset)
            
            # 执行查询
            transactions = query.all()
            
            logger.info(
                f"Transaction history retrieved: uid={uid}, count={len(transactions)}, "
                f"total={total_count}"
            )
            
            # 转换为字典列表
            result = []
            for txn in transactions:
                result.append({
                    'id': txn.id,
                    'type': txn.type,
                    'amount': txn.amount,  # 金额（元）
                    'balance_before': txn.balance_before,  # 交易前余额（元）
                    'balance_after': txn.balance_after,  # 交易后余额（元）
                    'merchant_id': txn.merchant_id,
                    'related_txn_id': txn.related_txn_id,
                    'remark': txn.remark,
                    'operator_id': txn.operator_id,
                    'created_at': txn.created_at.isoformat()
                })
            
            return {
                'transactions': result,
                'total_count': total_count
            }
            
        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve transaction history: {str(e)}", exc_info=True)
            raise
    
    def process_event_recharge(
        self,
        event_id: int,
        card_uid: str,
        amount_yuan: float,
        operator_id: Optional[str] = None,
        remark: Optional[str] = None
    ) -> TransactionResult:
        """
        处理活动模式充值交易。
        
        流程：
        1. 验证活动允许充值
        2. 通过 card_uid 查找参与者
        3. 获取或创建账户
        4. 调用 LedgerService 追加贷方记录
        
        Args:
            event_id: 活动ID
            card_uid: NFC卡片UID
            amount_yuan: 充值金额（元）
            operator_id: 操作员ID（可选）
            remark: 备注（可选）
            
        Returns:
            TransactionResult: 交易结果
            
        Raises:
            EventNotFoundError: 活动不存在
            EventInactiveError: 活动不允许充值
            ParticipantNotFoundError: 参与者不存在
        """
        from services.event_service import EventService
        from services.participant_service import ParticipantService
        from services.account_service import AccountService
        
        try:
            # 1. 验证活动允许充值
            event_service = EventService(self.db)
            event = event_service.validate_event_for_recharge(event_id)
            
            # 2. 通过 card_uid 查找参与者
            participant_service = ParticipantService(self.db)
            participant = participant_service.get_participant_by_card(card_uid)
            
            # 3. 获取或创建账户
            account_service = AccountService(self.db)
            account = account_service.get_or_create_account(
                participant_id=participant.id,
                event_id=event_id
            )
            
            # 4. 调用 LedgerService 追加贷方记录
            ledger_entry = self.ledger_service.append_credit_to_account(
                account_id=account.id,
                amount_yuan=amount_yuan,
                transaction_type="recharge",
                event_id=event_id,
                participant_id=participant.id,
                operator_id=operator_id,
                remark=remark
            )
            
            logger.info(
                f"Event recharge successful: event_id={event_id}, card_uid={card_uid}, "
                f"participant_id={participant.id}, amount={amount_yuan} yuan, "
                f"txn_id={ledger_entry.transaction_id}, "
                f"balance: {ledger_entry.balance_before} -> {ledger_entry.balance_after} yuan"
            )
            
            return TransactionResult(
                success=True,
                new_balance=ledger_entry.balance_after,
                transaction_id=ledger_entry.transaction_id,
                balance_before=ledger_entry.balance_before
            )
            
        except Exception as e:
            logger.warning(f"Event recharge failed: {str(e)}")
            raise
    
    def process_event_payment(
        self,
        event_id: int,
        card_uid: str,
        amount_yuan: float,
        merchant_id: Optional[str] = None,
        remark: Optional[str] = None
    ) -> TransactionResult:
        """
        处理活动模式消费交易。
        
        流程：
        1. 验证活动允许消费
        2. 通过 card_uid 查找参与者
        3. 获取或创建账户
        4. 调用 LedgerService 追加借方记录
        
        Args:
            event_id: 活动ID
            card_uid: NFC卡片UID
            amount_yuan: 消费金额（元）
            merchant_id: 商户ID（可选）
            remark: 备注（可选）
            
        Returns:
            TransactionResult: 交易结果
            
        Raises:
            EventNotFoundError: 活动不存在
            EventInactiveError: 活动不允许消费
            ParticipantNotFoundError: 参与者不存在
            InsufficientFundsError: 余额不足
        """
        from services.event_service import EventService
        from services.participant_service import ParticipantService
        from services.account_service import AccountService
        
        try:
            # 1. 验证活动允许消费
            event_service = EventService(self.db)
            event = event_service.validate_event_for_consume(event_id)
            
            # 2. 通过 card_uid 查找参与者
            participant_service = ParticipantService(self.db)
            participant = participant_service.get_participant_by_card(card_uid)
            
            # 3. 获取或创建账户
            account_service = AccountService(self.db)
            account = account_service.get_or_create_account(
                participant_id=participant.id,
                event_id=event_id
            )
            
            # 4. 调用 LedgerService 追加借方记录
            ledger_entry = self.ledger_service.append_debit_from_account(
                account_id=account.id,
                amount_yuan=amount_yuan,
                transaction_type="pay",
                event_id=event_id,
                participant_id=participant.id,
                merchant_id=merchant_id,
                remark=remark
            )
            
            logger.info(
                f"Event payment successful: event_id={event_id}, card_uid={card_uid}, "
                f"participant_id={participant.id}, amount={amount_yuan} yuan, "
                f"txn_id={ledger_entry.transaction_id}, "
                f"balance: {ledger_entry.balance_before} -> {ledger_entry.balance_after} yuan"
            )
            
            return TransactionResult(
                success=True,
                new_balance=ledger_entry.balance_after,
                transaction_id=ledger_entry.transaction_id,
                balance_before=ledger_entry.balance_before
            )
            
        except Exception as e:
            logger.warning(f"Event payment failed: {str(e)}")
            raise
    
    def get_event_transaction_history(
        self,
        event_id: int,
        participant_id: Optional[int] = None,
        transaction_types: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict:
        """
        获取活动交易历史记录。
        
        Args:
            event_id: 活动ID
            participant_id: 参与者ID（可选，用于过滤特定参与者）
            transaction_types: 交易类型列表（可选，用于过滤特定类型）
            start_date: 开始日期（ISO格式，可选）
            end_date: 结束日期（ISO格式，可选）
            limit: 返回记录数限制
            offset: 偏移量
            
        Returns:
            Dict: 包含交易列表和总数
            
        Raises:
            EventNotFoundError: 活动不存在
        """
        from services.event_service import EventService, EventNotFoundError
        
        try:
            # 验证活动存在（不存在则返回空结果）
            event_service = EventService(self.db)
            try:
                event = event_service.get_event(event_id)
            except EventNotFoundError:
                logger.warning(f"Event {event_id} not found, returning empty transaction list")
                return {
                    'transactions': [],
                    'total_count': 0
                }
            
            # 构建查询
            query = self.db.query(Transaction).filter(Transaction.event_id == event_id)
            
            # 应用参与者过滤
            if participant_id is not None:
                query = query.filter(Transaction.participant_id == participant_id)
            
            # 应用交易类型过滤
            if transaction_types:
                query = query.filter(Transaction.type.in_(transaction_types))
            
            # 应用日期过滤
            if start_date:
                from datetime import datetime
                start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(Transaction.created_at >= start_datetime)
            
            if end_date:
                from datetime import datetime
                end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.filter(Transaction.created_at <= end_datetime)
            
            # 获取总数
            total_count = query.count()
            
            # 排序并分页
            query = query.order_by(Transaction.created_at.desc(), Transaction.id.desc())
            query = query.limit(limit).offset(offset)
            
            # 执行查询
            transactions = query.all()
            
            logger.info(
                f"Event transaction history retrieved: event_id={event_id}, "
                f"participant_id={participant_id}, count={len(transactions)}, "
                f"total={total_count}"
            )
            
            # 转换为字典列表
            result = []
            for txn in transactions:
                txn_dict = {
                    'id': txn.id,
                    'type': txn.type,
                    'amount': txn.amount,  # 金额（元）
                    'balance_before': txn.balance_before,  # 交易前余额（元）
                    'balance_after': txn.balance_after,  # 交易后余额（元）
                    'participant_id': txn.participant_id,
                    'card_uid': txn.card_uid,
                    'booth_id': txn.booth_id if hasattr(txn, 'booth_id') else None,  # 安全访问
                    'product_id': txn.product_id if hasattr(txn, 'product_id') else None,  # 安全访问
                    'merchant_id': txn.merchant_id,
                    'related_txn_id': txn.related_txn_id,
                    'remark': txn.remark,
                    'operator_id': txn.operator_id,
                    'created_at': txn.created_at.isoformat() if txn.created_at else None
                }
                result.append(txn_dict)
            
            return {
                'transactions': result,
                'total_count': total_count
            }
            
        except Exception as e:
            logger.error(
                f"Failed to retrieve event transaction history: {str(e)}",
                exc_info=True
            )
            raise
    
    def get_leaderboard(
        self,
        leaderboard_type: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        生成排行榜。
        
        Args:
            leaderboard_type: 排行榜类型（'spending' 或 'income'）
            limit: 返回记录数限制
            
        Returns:
            List[Dict]: 排行榜列表
            
        Raises:
            ValueError: 排行榜类型无效
        """
        try:
            # 验证排行榜类型
            if leaderboard_type not in ['spending', 'income']:
                raise ValueError(
                    f"Invalid leaderboard type: {leaderboard_type}. "
                    f"Must be 'spending' or 'income'"
                )
            
            # 确定交易类型
            if leaderboard_type == 'spending':
                transaction_type = 'pay'
            else:  # income
                transaction_type = 'recharge'
            
            # 聚合查询
            from sqlalchemy import func
            query = self.db.query(
                Transaction.uid,
                func.sum(Transaction.amount).label('total_amount')
            ).filter(
                Transaction.type == transaction_type
            ).group_by(
                Transaction.uid
            ).order_by(
                func.sum(Transaction.amount).desc()
            ).limit(limit)
            
            # 执行查询
            results = query.all()
            
            logger.info(
                f"Leaderboard generated: type={leaderboard_type}, count={len(results)}"
            )
            
            # 转换为字典列表
            leaderboard = []
            for rank, (uid, total_amount) in enumerate(results, start=1):
                leaderboard.append({
                    'uid': uid,
                    'total_amount': float(total_amount),  # 金额已为元
                    'rank': rank
                })
            
            return leaderboard
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate leaderboard: {str(e)}", exc_info=True)
            raise
    
    def process_booth_payment(
        self,
        event_id: int,
        card_uid: str,
        booth_id: int,
        amount_yuan: float,
        operator_id: int,
        product_id: Optional[int] = None,
        remark: Optional[str] = None
    ) -> TransactionResult:
        """
        处理摊位支付交易（Booth Management System）。
        
        验证流程:
        1. 验证活动允许消费
        2. 验证摊位属于活动
        3. 验证操作员有权限操作该摊位
        4. 如果提供 product_id，验证商品属于该摊位
        5. 执行支付交易，记录 booth_id、product_id、operator_id
        
        Args:
            event_id: 活动ID
            card_uid: NFC卡片UID
            booth_id: 摊位ID
            amount_yuan: 消费金额（元）
            operator_id: 操作员用户ID
            product_id: 商品ID（可选）
            remark: 备注（可选）
            
        Returns:
            TransactionResult: 交易结果
            
        Raises:
            EventNotFoundError: 活动不存在
            EventInactiveError: 活动不允许消费
            ParticipantNotFoundError: 参与者不存在
            InsufficientFundsError: 余额不足
            ValidationError: 验证错误（摊位不属于活动、商品不属于摊位等）
            
        Validates Requirements:
            - Requirement 10.1: Require event_id, booth_id, and operator_id
            - Requirement 10.2: Accept optional product_id
            - Requirement 10.3: Verify product belongs to booth
            - Requirement 10.4: Verify booth belongs to event
            - Requirement 10.5: Verify operator has permission
            - Requirement 10.6: Record booth_id, product_id, operator_id
        """
        from services.event_service import EventService
        from services.participant_service import ParticipantService
        from services.account_service import AccountService
        
        try:
            # 1. 验证活动允许消费
            event_service = EventService(self.db)
            event = event_service.validate_event_for_consume(event_id)
            
            # 2. 验证摊位属于活动
            booth = self.db.query(Booth).filter(Booth.id == booth_id).first()
            if booth is None:
                raise ResourceNotFoundError(
                    f"Booth with id {booth_id} not found",
                    error_code="BOOTH_NOT_FOUND"
                )
            
            if booth.event_id != event_id:
                raise ValidationError(
                    f"Booth {booth_id} does not belong to event {event_id}",
                    error_code="BOOTH_NOT_IN_EVENT"
                )
            
            # 3. 验证操作员有权限操作该摊位
            operator = self.db.query(User).filter(User.id == operator_id).first()
            if operator is None:
                raise ResourceNotFoundError(
                    f"Operator with id {operator_id} not found",
                    error_code="OPERATOR_NOT_FOUND"
                )
            
            # 权限验证：super_admin 和 event_admin 可以操作所有摊位
            # booth_cashier 只能操作自己的摊位
            if operator.role == 'booth_cashier':
                if operator.booth_id != booth_id:
                    raise ValidationError(
                        f"Operator {operator_id} does not have permission to operate booth {booth_id}",
                        error_code="OPERATOR_PERMISSION_DENIED"
                    )
            elif operator.role not in ('super_admin', 'event_admin'):
                raise ValidationError(
                    f"Operator role '{operator.role}' cannot process payments",
                    error_code="OPERATOR_ROLE_NOT_ALLOWED"
                )
            
            # 4. 如果提供 product_id，验证商品属于该摊位
            if product_id is not None:
                product = self.db.query(Product).filter(Product.id == product_id).first()
                if product is None:
                    raise ResourceNotFoundError(
                        f"Product with id {product_id} not found",
                        error_code="PRODUCT_NOT_FOUND"
                    )
                
                if product.booth_id != booth_id:
                    raise ValidationError(
                        f"Product {product_id} does not belong to booth {booth_id}",
                        error_code="PRODUCT_NOT_IN_BOOTH"
                    )
            
            # 5. 通过 card_uid 查找参与者
            participant_service = ParticipantService(self.db)
            participant = participant_service.get_participant_by_card(card_uid)
            
            # 6. 获取或创建账户
            account_service = AccountService(self.db)
            account = account_service.get_or_create_account(
                participant_id=participant.id,
                event_id=event_id
            )
            
            # 7. 调用 LedgerService 追加借方记录，包含摊位和商品信息
            ledger_entry = self.ledger_service.append_debit_from_account(
                account_id=account.id,
                amount_yuan=amount_yuan,
                transaction_type="pay",
                event_id=event_id,
                participant_id=participant.id,
                merchant_id=None,
                remark=remark,
                booth_id=booth_id,
                product_id=product_id,
                operator_id=operator_id
            )
            
            logger.info(
                f"Booth payment successful: event_id={event_id}, card_uid={card_uid}, "
                f"booth_id={booth_id}, product_id={product_id}, operator_id={operator_id}, "
                f"amount={amount_yuan} yuan, txn_id={ledger_entry.transaction_id}, "
                f"balance: {ledger_entry.balance_before} -> {ledger_entry.balance_after} yuan"
            )
            
            return TransactionResult(
                success=True,
                new_balance=ledger_entry.balance_after,
                transaction_id=ledger_entry.transaction_id,
                balance_before=ledger_entry.balance_before
            )
            
        except Exception as e:
            logger.warning(f"Booth payment failed: {str(e)}")
            raise
    
    def get_booth_transactions(
        self,
        booth_id: int,
        product_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict:
        """
        获取摊位交易记录。
        
        Args:
            booth_id: 摊位ID
            product_id: 商品ID（可选，用于过滤特定商品的交易）
            start_date: 开始日期（ISO格式，可选）
            end_date: 结束日期（ISO格式，可选）
            limit: 返回记录数限制
            offset: 偏移量
            
        Returns:
            Dict: 包含交易列表和总数
            
        Raises:
            ResourceNotFoundError: 摊位不存在或商品不存在
            ValidationError: 商品不属于指定摊位
            
        Validates Requirements:
            - Requirement 11.4: Support filtering transactions by booth_id and product_id
            - Requirement 11.5: Support filtering transactions by booth_id
            - Requirement 11.6: Support filtering transactions by product_id
        """
        try:
            # 验证摊位存在
            booth = self.db.query(Booth).filter(Booth.id == booth_id).first()
            if booth is None:
                raise ResourceNotFoundError(
                    f"Booth with id {booth_id} not found",
                    error_code="BOOTH_NOT_FOUND"
                )
            
            # 如果提供了 product_id，验证商品存在且属于该摊位
            if product_id is not None:
                product = self.db.query(Product).filter(Product.id == product_id).first()
                if product is None:
                    raise ResourceNotFoundError(
                        f"Product with id {product_id} not found",
                        error_code="PRODUCT_NOT_FOUND"
                    )
                
                if product.booth_id != booth_id:
                    raise ValidationError(
                        f"Product {product_id} does not belong to booth {booth_id}",
                        error_code="PRODUCT_NOT_IN_BOOTH"
                    )
            
            # 构建查询
            query = self.db.query(Transaction).filter(Transaction.booth_id == booth_id)
            
            # 应用商品过滤
            if product_id is not None:
                query = query.filter(Transaction.product_id == product_id)
            
            # 应用日期过滤
            if start_date:
                from datetime import datetime
                start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(Transaction.created_at >= start_datetime)
            
            if end_date:
                from datetime import datetime
                end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.filter(Transaction.created_at <= end_datetime)
            
            # 获取总数
            total_count = query.count()
            
            # 排序并分页
            query = query.order_by(Transaction.created_at.desc(), Transaction.id.desc())
            query = query.limit(limit).offset(offset)
            
            # 执行查询
            transactions = query.all()
            
            logger.info(
                f"Booth transaction history retrieved: booth_id={booth_id}, "
                f"product_id={product_id}, count={len(transactions)}, total={total_count}"
            )
            
            # 转换为字典列表
            result = []
            for txn in transactions:
                result.append({
                    'id': txn.id,
                    'type': txn.type,
                    'amount': txn.amount,  # 金额（元）
                    'balance_before': txn.balance_before,  # 交易前余额（元）
                    'balance_after': txn.balance_after,  # 交易后余额（元）
                    'participant_id': txn.participant_id,
                    'card_uid': txn.card_uid,
                    'booth_id': txn.booth_id,
                    'product_id': txn.product_id,
                    'operator_id': txn.operator_id,
                    'merchant_id': txn.merchant_id,
                    'related_txn_id': txn.related_txn_id,
                    'remark': txn.remark,
                    'created_at': txn.created_at.isoformat()
                })
            
            return {
                'transactions': result,
                'total_count': total_count
            }
            
        except Exception as e:
            logger.error(
                f"Failed to retrieve booth transaction history: {str(e)}",
                exc_info=True
            )
            raise

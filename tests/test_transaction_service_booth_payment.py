"""
Tests for TransactionService.process_booth_payment method.

验证摊位支付功能的正确性。
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

from core.database import Base
from models.event import Event
from models.participant import Participant
from models.account import Account
from models.booth import Booth
from models.product import Product
from models.user import User
from services.transaction_service import TransactionService
from services.auth_service import AuthService
from core.exceptions import ValidationError, ResourceNotFoundError


@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_data(db_session):
    """创建测试数据"""
    # 创建活动
    event = Event(
        name="Test Event",
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        status="active",
        recharge_enabled=True,
        consume_enabled=True
    )
    db_session.add(event)
    db_session.flush()
    
    # 创建摊位
    booth = Booth(
        event_id=event.id,
        name="Test Booth",
        class_name="Class 1",
        status="active"
    )
    db_session.add(booth)
    db_session.flush()
    
    # 创建商品
    product = Product(
        booth_id=booth.id,
        name="Test Product",
        price=500,  # 5元
        cost_price=300,
        stock=100,
        enabled=True
    )
    db_session.add(product)
    db_session.flush()
    
    # 创建操作员（booth_cashier）
    auth_service = AuthService(db_session)
    password_hash = auth_service.hash_password("password123")
    
    operator = User(
        username="cashier1",
        password_hash=password_hash,
        role="booth_cashier",
        booth_id=booth.id,
        status="active"
    )
    db_session.add(operator)
    db_session.flush()
    
    # 创建参与者
    participant = Participant(
        name="Test Participant",
        card_uid="A1B2C3D4",
        status="active"
    )
    db_session.add(participant)
    db_session.flush()
    
    # 创建账户并充值
    account = Account(
        participant_id=participant.id,
        event_id=event.id,
        balance=10000  # 100元
    )
    db_session.add(account)
    db_session.commit()
    
    return {
        "event": event,
        "booth": booth,
        "product": product,
        "operator": operator,
        "participant": participant,
        "account": account
    }


def test_process_booth_payment_success(db_session, test_data):
    """测试成功的摊位支付"""
    service = TransactionService(db_session)
    
    result = service.process_booth_payment(
        event_id=test_data["event"].id,
        card_uid=test_data["participant"].card_uid,
        booth_id=test_data["booth"].id,
        amount_yuan=5.0,
        operator_id=test_data["operator"].id,
        product_id=test_data["product"].id,
        remark="Test payment"
    )
    
    assert result.success is True
    assert result.new_balance == 9500  # 10000 - 500
    assert result.balance_before == 10000
    assert result.transaction_id is not None


def test_process_booth_payment_without_product(db_session, test_data):
    """测试不指定商品的摊位支付"""
    service = TransactionService(db_session)
    
    result = service.process_booth_payment(
        event_id=test_data["event"].id,
        card_uid=test_data["participant"].card_uid,
        booth_id=test_data["booth"].id,
        amount_yuan=3.0,
        operator_id=test_data["operator"].id,
        product_id=None,
        remark="Payment without product"
    )
    
    assert result.success is True
    assert result.new_balance == 9700  # 10000 - 300
    assert result.transaction_id is not None


def test_process_booth_payment_booth_not_in_event(db_session, test_data):
    """测试摊位不属于活动的情况"""
    service = TransactionService(db_session)
    
    # 创建另一个活动
    other_event = Event(
        name="Other Event",
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        status="active",
        recharge_enabled=True,
        consume_enabled=True
    )
    db_session.add(other_event)
    db_session.commit()
    
    with pytest.raises(ValidationError) as exc_info:
        service.process_booth_payment(
            event_id=other_event.id,
            card_uid=test_data["participant"].card_uid,
            booth_id=test_data["booth"].id,
            amount_yuan=5.0,
            operator_id=test_data["operator"].id
        )
    
    assert "does not belong to event" in str(exc_info.value)


def test_process_booth_payment_product_not_in_booth(db_session, test_data):
    """测试商品不属于摊位的情况"""
    service = TransactionService(db_session)
    
    # 创建另一个摊位和商品
    other_booth = Booth(
        event_id=test_data["event"].id,
        name="Other Booth",
        class_name="Class 2",
        status="active"
    )
    db_session.add(other_booth)
    db_session.flush()
    
    other_product = Product(
        booth_id=other_booth.id,
        name="Other Product",
        price=300,
        enabled=True
    )
    db_session.add(other_product)
    db_session.commit()
    
    with pytest.raises(ValidationError) as exc_info:
        service.process_booth_payment(
            event_id=test_data["event"].id,
            card_uid=test_data["participant"].card_uid,
            booth_id=test_data["booth"].id,
            amount_yuan=5.0,
            operator_id=test_data["operator"].id,
            product_id=other_product.id  # 使用其他摊位的商品
        )
    
    assert "does not belong to booth" in str(exc_info.value)


def test_process_booth_payment_operator_permission_denied(db_session, test_data):
    """测试操作员无权限操作摊位的情况"""
    service = TransactionService(db_session)
    auth_service = AuthService(db_session)
    
    # 创建另一个摊位
    other_booth = Booth(
        event_id=test_data["event"].id,
        name="Other Booth",
        class_name="Class 2",
        status="active"
    )
    db_session.add(other_booth)
    db_session.flush()
    
    # 创建另一个收银员，绑定到其他摊位
    password_hash = auth_service.hash_password("password123")
    other_operator = User(
        username="cashier2",
        password_hash=password_hash,
        role="booth_cashier",
        booth_id=other_booth.id,
        status="active"
    )
    db_session.add(other_operator)
    db_session.commit()
    
    with pytest.raises(ValidationError) as exc_info:
        service.process_booth_payment(
            event_id=test_data["event"].id,
            card_uid=test_data["participant"].card_uid,
            booth_id=test_data["booth"].id,
            amount_yuan=5.0,
            operator_id=other_operator.id  # 使用其他摊位的收银员
        )
    
    assert "does not have permission" in str(exc_info.value)


def test_process_booth_payment_event_admin_can_operate_any_booth(db_session, test_data):
    """测试活动管理员可以操作任何摊位"""
    service = TransactionService(db_session)
    auth_service = AuthService(db_session)
    
    # 创建活动管理员
    password_hash = auth_service.hash_password("password123")
    event_admin = User(
        username="event_admin",
        password_hash=password_hash,
        role="event_admin",
        booth_id=None,
        status="active"
    )
    db_session.add(event_admin)
    db_session.commit()
    
    result = service.process_booth_payment(
        event_id=test_data["event"].id,
        card_uid=test_data["participant"].card_uid,
        booth_id=test_data["booth"].id,
        amount_yuan=5.0,
        operator_id=event_admin.id
    )
    
    assert result.success is True
    assert result.new_balance == 9500


def test_process_booth_payment_operator_not_found(db_session, test_data):
    """测试操作员不存在的情况"""
    service = TransactionService(db_session)
    
    with pytest.raises(ResourceNotFoundError) as exc_info:
        service.process_booth_payment(
            event_id=test_data["event"].id,
            card_uid=test_data["participant"].card_uid,
            booth_id=test_data["booth"].id,
            amount_yuan=5.0,
            operator_id=99999  # 不存在的操作员ID
        )
    
    assert "Operator with id 99999 not found" in str(exc_info.value)


def test_process_booth_payment_booth_not_found(db_session, test_data):
    """测试摊位不存在的情况"""
    service = TransactionService(db_session)
    
    with pytest.raises(ResourceNotFoundError) as exc_info:
        service.process_booth_payment(
            event_id=test_data["event"].id,
            card_uid=test_data["participant"].card_uid,
            booth_id=99999,  # 不存在的摊位ID
            amount_yuan=5.0,
            operator_id=test_data["operator"].id
        )
    
    assert "Booth with id 99999 not found" in str(exc_info.value)


def test_process_booth_payment_product_not_found(db_session, test_data):
    """测试商品不存在的情况"""
    service = TransactionService(db_session)
    
    with pytest.raises(ResourceNotFoundError) as exc_info:
        service.process_booth_payment(
            event_id=test_data["event"].id,
            card_uid=test_data["participant"].card_uid,
            booth_id=test_data["booth"].id,
            amount_yuan=5.0,
            operator_id=test_data["operator"].id,
            product_id=99999  # 不存在的商品ID
        )
    
    assert "Product with id 99999 not found" in str(exc_info.value)

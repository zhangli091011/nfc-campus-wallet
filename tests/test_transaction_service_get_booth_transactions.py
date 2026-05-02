"""
Tests for TransactionService.get_booth_transactions method.

验证摊位交易查询功能的正确性，包括按 booth_id、product_id 和日期范围过滤。
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone, timedelta

from core.database import Base
from core.config import load_settings
from models.event import Event
from models.participant import Participant
from models.account import Account
from models.booth import Booth
from models.product import Product
from models.user import User
from models.transaction import Transaction
from services.transaction_service import TransactionService
from core.security import hash_password
from core.exceptions import ValidationError, ResourceNotFoundError


@pytest.fixture(scope="session", autouse=True)
def load_test_settings():
    """加载测试配置"""
    load_settings()


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
    product1 = Product(
        booth_id=booth.id,
        name="Product 1",
        price=500,  # 5元
        cost_price=300,
        stock=100,
        enabled=True
    )
    product2 = Product(
        booth_id=booth.id,
        name="Product 2",
        price=800,  # 8元
        cost_price=500,
        stock=50,
        enabled=True
    )
    db_session.add(product1)
    db_session.add(product2)
    db_session.flush()
    
    # 创建操作员
    password_hash_value = hash_password("password123")
    
    operator = User(
        username="cashier1",
        password_hash=password_hash_value,
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
    
    # 创建账户
    account = Account(
        participant_id=participant.id,
        event_id=event.id,
        balance=10000  # 100元
    )
    db_session.add(account)
    db_session.flush()
    
    # 创建交易记录
    now = datetime.now(timezone.utc)
    
    # 交易1: Product 1, 今天
    txn1 = Transaction(
        event_id=event.id,
        participant_id=participant.id,
        account_id=account.id,
        card_uid=participant.card_uid,
        type="pay",
        amount=500,
        balance_before=10000,
        balance_after=9500,
        booth_id=booth.id,
        product_id=product1.id,
        booth_operator_id=operator.id,
        created_at=now
    )
    
    # 交易2: Product 2, 今天
    txn2 = Transaction(
        event_id=event.id,
        participant_id=participant.id,
        account_id=account.id,
        card_uid=participant.card_uid,
        type="pay",
        amount=800,
        balance_before=9500,
        balance_after=8700,
        booth_id=booth.id,
        product_id=product2.id,
        booth_operator_id=operator.id,
        created_at=now
    )
    
    # 交易3: Product 1, 昨天
    txn3 = Transaction(
        event_id=event.id,
        participant_id=participant.id,
        account_id=account.id,
        card_uid=participant.card_uid,
        type="pay",
        amount=500,
        balance_before=8700,
        balance_after=8200,
        booth_id=booth.id,
        product_id=product1.id,
        booth_operator_id=operator.id,
        created_at=now - timedelta(days=1)
    )
    
    # 交易4: 无商品, 今天
    txn4 = Transaction(
        event_id=event.id,
        participant_id=participant.id,
        account_id=account.id,
        card_uid=participant.card_uid,
        type="pay",
        amount=300,
        balance_before=8200,
        balance_after=7900,
        booth_id=booth.id,
        product_id=None,
        booth_operator_id=operator.id,
        created_at=now
    )
    
    db_session.add_all([txn1, txn2, txn3, txn4])
    db_session.commit()
    
    return {
        "event": event,
        "booth": booth,
        "product1": product1,
        "product2": product2,
        "operator": operator,
        "participant": participant,
        "account": account,
        "transactions": [txn1, txn2, txn3, txn4]
    }


def test_get_booth_transactions_all(db_session, test_data):
    """测试获取摊位所有交易"""
    service = TransactionService(db_session)
    
    result = service.get_booth_transactions(
        booth_id=test_data["booth"].id
    )
    
    assert result["total_count"] == 4
    assert len(result["transactions"]) == 4


def test_get_booth_transactions_filter_by_product(db_session, test_data):
    """测试按商品过滤交易"""
    service = TransactionService(db_session)
    
    # 过滤 Product 1 的交易
    result = service.get_booth_transactions(
        booth_id=test_data["booth"].id,
        product_id=test_data["product1"].id
    )
    
    assert result["total_count"] == 2
    assert len(result["transactions"]) == 2
    for txn in result["transactions"]:
        assert txn["product_id"] == test_data["product1"].id


def test_get_booth_transactions_filter_by_product2(db_session, test_data):
    """测试按商品2过滤交易"""
    service = TransactionService(db_session)
    
    # 过滤 Product 2 的交易
    result = service.get_booth_transactions(
        booth_id=test_data["booth"].id,
        product_id=test_data["product2"].id
    )
    
    assert result["total_count"] == 1
    assert len(result["transactions"]) == 1
    assert result["transactions"][0]["product_id"] == test_data["product2"].id


def test_get_booth_transactions_filter_by_date_range(db_session, test_data):
    """测试按日期范围过滤交易"""
    service = TransactionService(db_session)
    
    # 只查询今天的交易
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = today.isoformat()
    
    result = service.get_booth_transactions(
        booth_id=test_data["booth"].id,
        start_date=start_date
    )
    
    # 应该有3条今天的交易（txn1, txn2, txn4）
    assert result["total_count"] == 3
    assert len(result["transactions"]) == 3


def test_get_booth_transactions_filter_by_product_and_date(db_session, test_data):
    """测试同时按商品和日期过滤交易"""
    service = TransactionService(db_session)
    
    # 查询今天的 Product 1 交易
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = today.isoformat()
    
    result = service.get_booth_transactions(
        booth_id=test_data["booth"].id,
        product_id=test_data["product1"].id,
        start_date=start_date
    )
    
    # 应该只有1条交易（txn1）
    assert result["total_count"] == 1
    assert len(result["transactions"]) == 1
    assert result["transactions"][0]["product_id"] == test_data["product1"].id


def test_get_booth_transactions_pagination(db_session, test_data):
    """测试分页功能"""
    service = TransactionService(db_session)
    
    # 第一页，每页2条
    result = service.get_booth_transactions(
        booth_id=test_data["booth"].id,
        limit=2,
        offset=0
    )
    
    assert result["total_count"] == 4
    assert len(result["transactions"]) == 2
    
    # 第二页
    result = service.get_booth_transactions(
        booth_id=test_data["booth"].id,
        limit=2,
        offset=2
    )
    
    assert result["total_count"] == 4
    assert len(result["transactions"]) == 2


def test_get_booth_transactions_booth_not_found(db_session, test_data):
    """测试摊位不存在的情况"""
    service = TransactionService(db_session)
    
    with pytest.raises(ResourceNotFoundError) as exc_info:
        service.get_booth_transactions(
            booth_id=99999  # 不存在的摊位ID
        )
    
    assert "Booth with id 99999 not found" in str(exc_info.value)


def test_get_booth_transactions_product_not_found(db_session, test_data):
    """测试商品不存在的情况"""
    service = TransactionService(db_session)
    
    with pytest.raises(ResourceNotFoundError) as exc_info:
        service.get_booth_transactions(
            booth_id=test_data["booth"].id,
            product_id=99999  # 不存在的商品ID
        )
    
    assert "Product with id 99999 not found" in str(exc_info.value)


def test_get_booth_transactions_product_not_in_booth(db_session, test_data):
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
        service.get_booth_transactions(
            booth_id=test_data["booth"].id,
            product_id=other_product.id  # 使用其他摊位的商品
        )
    
    assert "does not belong to booth" in str(exc_info.value)


def test_get_booth_transactions_response_format(db_session, test_data):
    """测试响应格式正确性"""
    service = TransactionService(db_session)
    
    result = service.get_booth_transactions(
        booth_id=test_data["booth"].id,
        limit=1
    )
    
    assert "transactions" in result
    assert "total_count" in result
    assert isinstance(result["transactions"], list)
    assert isinstance(result["total_count"], int)
    
    # 检查交易记录字段
    if len(result["transactions"]) > 0:
        txn = result["transactions"][0]
        assert "id" in txn
        assert "type" in txn
        assert "amount" in txn
        assert "balance_before" in txn
        assert "balance_after" in txn
        assert "booth_id" in txn
        assert "product_id" in txn
        assert "operator_id" in txn
        assert "created_at" in txn

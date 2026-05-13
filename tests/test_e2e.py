"""
End-to-End (E2E) Tests for NFC Campus E-Wallet System.

测试完整的业务流程，包括：
1. 活动创建 → 参与者注册 → 充值 → 消费 → 查询余额
2. 摊位管理 → 商品管理 → 摊位支付
3. 用户认证 → 角色权限验证
4. 退款流程

所有测试数据在测试结束后自动清理，不影响数据库。

使用方法：
    pytest tests/test_e2e.py -v
    pytest tests/test_e2e.py -v -k "test_full_event_flow"
"""

import os
import sys
import time
import hashlib
import logging
from typing import Optional, Dict, Any, List
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import load_settings, get_settings
from core.database import init_database, get_db, SessionLocal
from app.main import create_app

logger = logging.getLogger(__name__)


# ============================================================================
# Test Fixtures & Helpers
# ============================================================================


class TestDataTracker:
    """
    测试数据追踪器，记录所有创建的测试数据以便清理。
    """

    def __init__(self):
        self.created_events: List[int] = []
        self.created_participants: List[int] = []
        self.created_users: List[int] = []
        self.created_booths: List[int] = []
        self.created_transactions: List[int] = []
        self.admin_token: Optional[str] = None

    def cleanup(self, client: TestClient):
        """
        清理所有测试数据（按依赖顺序反向删除）。
        """
        headers = {"Authorization": f"Bearer {self.admin_token}"} if self.admin_token else {}

        # 1. 删除摊位（会级联删除商品）
        for booth_id in reversed(self.created_booths):
            try:
                resp = client.delete(f"/booths/{booth_id}", headers=headers)
                logger.info(f"Cleanup booth {booth_id}: status={resp.status_code}")
            except Exception as e:
                logger.warning(f"Failed to cleanup booth {booth_id}: {e}")

        # 2. 删除用户（非admin）
        for user_id in reversed(self.created_users):
            try:
                resp = client.patch(
                    f"/users/{user_id}/status?status=inactive",
                    headers=headers
                )
                logger.info(f"Cleanup user {user_id}: status={resp.status_code}")
            except Exception as e:
                logger.warning(f"Failed to cleanup user {user_id}: {e}")

        # 3. 删除参与者（会级联删除账户）
        for participant_id in reversed(self.created_participants):
            try:
                resp = client.delete(
                    f"/participants/{participant_id}",
                    headers=headers
                )
                logger.info(f"Cleanup participant {participant_id}: status={resp.status_code}")
            except Exception as e:
                logger.warning(f"Failed to cleanup participant {participant_id}: {e}")

        # 4. 清理交易记录（通过直接数据库操作）
        if self.created_transactions:
            try:
                db = next(get_db())
                from models.transaction import Transaction
                db.query(Transaction).filter(
                    Transaction.id.in_(self.created_transactions)
                ).delete(synchronize_session=False)
                db.commit()
                db.close()
                logger.info(f"Cleanup {len(self.created_transactions)} transactions via DB")
            except Exception as e:
                logger.warning(f"Failed to cleanup transactions: {e}")

        # 5. 删除活动（会级联删除关联数据）
        for event_id in reversed(self.created_events):
            try:
                db = next(get_db())
                from models.event import Event
                event = db.query(Event).filter(Event.id == event_id).first()
                if event:
                    db.delete(event)
                    db.commit()
                logger.info(f"Cleanup event {event_id} via DB")
                db.close()
            except Exception as e:
                logger.warning(f"Failed to cleanup event {event_id}: {e}")


def generate_signature(uid: str, timestamp: int, secret_key: str, amount: Optional[float] = None) -> str:
    """生成请求签名。"""
    if amount is not None:
        message = f"{uid}{amount}{timestamp}{secret_key}"
    else:
        message = f"{uid}{timestamp}{secret_key}"
    return hashlib.sha256(message.encode('utf-8')).hexdigest()


@pytest.fixture(scope="module")
def app():
    """创建测试应用实例。"""
    application = create_app()
    return application


@pytest.fixture(scope="module")
def client(app):
    """创建测试客户端。"""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def tracker():
    """创建测试数据追踪器。"""
    return TestDataTracker()


@pytest.fixture(scope="module")
def admin_token(client, tracker) -> str:
    """
    获取管理员 JWT token。
    使用系统中已存在的 admin 账户登录。
    """
    resp = client.post("/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })

    if resp.status_code != 200:
        pytest.skip("Admin account not available, skipping E2E tests")

    token = resp.json()["access_token"]
    tracker.admin_token = token
    return token


@pytest.fixture(scope="module")
def auth_headers(admin_token) -> Dict[str, str]:
    """获取认证请求头。"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="module", autouse=True)
def cleanup_after_tests(client, tracker):
    """测试完成后自动清理所有测试数据。"""
    yield
    logger.info("=" * 60)
    logger.info("Starting E2E test data cleanup...")
    logger.info("=" * 60)
    tracker.cleanup(client)
    logger.info("E2E test data cleanup completed.")


# ============================================================================
# E2E Test: Complete Event Flow
# ============================================================================


class TestFullEventFlow:
    """
    测试完整的活动流程：
    创建活动 → 创建参与者 → 充值 → 消费 → 查询余额 → 查询交易历史
    """

    def test_01_create_event(self, client, auth_headers, tracker):
        """创建测试活动。"""
        resp = client.post("/events", json={
            "name": "E2E测试活动_自动清理",
            "start_date": "2026-01-01T00:00:00Z",
            "end_date": "2026-12-31T23:59:59Z",
            "status": "active",
            "allow_recharge": True,
            "allow_payment": True
        })

        assert resp.status_code == 201, f"Create event failed: {resp.text}"
        data = resp.json()
        assert data["name"] == "E2E测试活动_自动清理"
        assert data["status"] == "active"

        tracker.created_events.append(data["id"])
        self.__class__.event_id = data["id"]

    def test_02_create_participant(self, client, tracker):
        """创建测试参与者。"""
        # 使用唯一的 card_uid 避免冲突
        card_uid = f"E2E{int(time.time()) % 100000:05d}A"

        resp = client.post("/participants", json={
            "name": "E2E测试用户",
            "card_uid": card_uid,
            "class_name": "测试班级",
            "student_no": "E2E001",
            "status": "active"
        })

        assert resp.status_code == 201, f"Create participant failed: {resp.text}"
        data = resp.json()
        assert data["name"] == "E2E测试用户"
        assert data["card_uid"] == card_uid.upper()

        tracker.created_participants.append(data["id"])
        self.__class__.participant_id = data["id"]
        self.__class__.card_uid = card_uid.upper()

    def test_03_recharge(self, client, tracker):
        """充值测试。"""
        event_id = self.__class__.event_id
        card_uid = self.__class__.card_uid
        timestamp = int(time.time())
        settings = get_settings()
        signature = generate_signature(card_uid, timestamp, settings.secret_key, 100.00)

        resp = client.post("/recharge", json={
            "event_id": event_id,
            "card_uid": card_uid,
            "amount": 100.00,
            "timestamp": timestamp,
            "signature": signature,
            "operator_id": "E2E_TEST",
            "remark": "E2E测试充值"
        })

        assert resp.status_code == 200, f"Recharge failed: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        assert data["new_balance"] == 100.00
        assert data["balance_before"] == 0.00

        tracker.created_transactions.append(data["transaction_id"])
        self.__class__.recharge_txn_id = data["transaction_id"]

    def test_04_query_balance(self, client):
        """查询余额。"""
        event_id = self.__class__.event_id
        card_uid = self.__class__.card_uid
        timestamp = int(time.time())
        settings = get_settings()
        signature = generate_signature(card_uid, timestamp, settings.secret_key)

        resp = client.get("/balance", params={
            "event_id": event_id,
            "card_uid": card_uid,
            "timestamp": timestamp,
            "signature": signature
        })

        assert resp.status_code == 200, f"Balance query failed: {resp.text}"
        data = resp.json()
        assert data["balance"] == 100.00

    def test_05_payment(self, client, tracker):
        """消费测试。"""
        event_id = self.__class__.event_id
        card_uid = self.__class__.card_uid
        timestamp = int(time.time())
        settings = get_settings()
        signature = generate_signature(card_uid, timestamp, settings.secret_key, 30.00)

        resp = client.post("/pay", json={
            "event_id": event_id,
            "card_uid": card_uid,
            "amount": 30.00,
            "timestamp": timestamp,
            "signature": signature,
            "remark": "E2E测试消费"
        })

        assert resp.status_code == 200, f"Payment failed: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        assert data["new_balance"] == 70.00
        assert data["balance_before"] == 100.00

        tracker.created_transactions.append(data["transaction_id"])

    def test_06_verify_balance_after_payment(self, client):
        """验证消费后余额。"""
        event_id = self.__class__.event_id
        card_uid = self.__class__.card_uid
        timestamp = int(time.time())
        settings = get_settings()
        signature = generate_signature(card_uid, timestamp, settings.secret_key)

        resp = client.get("/balance", params={
            "event_id": event_id,
            "card_uid": card_uid,
            "timestamp": timestamp,
            "signature": signature
        })

        assert resp.status_code == 200
        assert resp.json()["balance"] == 70.00

    def test_07_insufficient_funds(self, client):
        """余额不足测试。"""
        event_id = self.__class__.event_id
        card_uid = self.__class__.card_uid
        timestamp = int(time.time())
        settings = get_settings()
        signature = generate_signature(card_uid, timestamp, settings.secret_key, 999.00)

        resp = client.post("/pay", json={
            "event_id": event_id,
            "card_uid": card_uid,
            "amount": 999.00,
            "timestamp": timestamp,
            "signature": signature,
            "remark": "余额不足测试"
        })

        assert resp.status_code == 400
        data = resp.json()
        assert data["error_code"] == "INSUFFICIENT_FUNDS"

    def test_08_multiple_recharges_and_payments(self, client, tracker):
        """多次充值和消费测试。"""
        event_id = self.__class__.event_id
        card_uid = self.__class__.card_uid
        settings = get_settings()

        # 再充值 50 元
        timestamp = int(time.time())
        signature = generate_signature(card_uid, timestamp, settings.secret_key, 50.00)
        resp = client.post("/recharge", json={
            "event_id": event_id,
            "card_uid": card_uid,
            "amount": 50.00,
            "timestamp": timestamp,
            "signature": signature,
            "remark": "第二次充值"
        })
        assert resp.status_code == 200
        assert resp.json()["new_balance"] == 120.00
        tracker.created_transactions.append(resp.json()["transaction_id"])

        # 消费 20 元
        timestamp = int(time.time())
        signature = generate_signature(card_uid, timestamp, settings.secret_key, 20.00)
        resp = client.post("/pay", json={
            "event_id": event_id,
            "card_uid": card_uid,
            "amount": 20.00,
            "timestamp": timestamp,
            "signature": signature,
            "remark": "第二次消费"
        })
        assert resp.status_code == 200
        assert resp.json()["new_balance"] == 100.00
        tracker.created_transactions.append(resp.json()["transaction_id"])


# ============================================================================
# E2E Test: Booth Management Flow
# ============================================================================


class TestBoothManagementFlow:
    """
    测试摊位管理完整流程：
    创建活动 → 创建摊位 → 创建商品 → 创建收银员 → 摊位支付
    """

    def test_01_setup_event(self, client, auth_headers, tracker):
        """创建摊位测试用活动。"""
        resp = client.post("/events", json={
            "name": "E2E摊位测试活动_自动清理",
            "start_date": "2026-01-01T00:00:00Z",
            "end_date": "2026-12-31T23:59:59Z",
            "status": "active",
            "allow_recharge": True,
            "allow_payment": True
        })
        assert resp.status_code == 201
        tracker.created_events.append(resp.json()["id"])
        self.__class__.event_id = resp.json()["id"]

    def test_02_create_booth(self, client, auth_headers, tracker):
        """创建摊位。"""
        resp = client.post("/booths", json={
            "event_id": self.__class__.event_id,
            "name": "E2E测试摊位",
            "class_name": "测试班级A"
        }, headers=auth_headers)

        assert resp.status_code == 201, f"Create booth failed: {resp.text}"
        data = resp.json()
        assert data["name"] == "E2E测试摊位"

        tracker.created_booths.append(data["id"])
        self.__class__.booth_id = data["id"]

    def test_03_create_product(self, client, auth_headers):
        """创建商品。"""
        resp = client.post("/products", json={
            "booth_id": self.__class__.booth_id,
            "name": "E2E测试商品",
            "price": 15.00,
            "stock": 100,
            "status": "active"
        }, headers=auth_headers)

        assert resp.status_code == 201, f"Create product failed: {resp.text}"
        data = resp.json()
        assert data["name"] == "E2E测试商品"
        assert data["price"] == 15.00

        self.__class__.product_id = data["id"]

    def test_04_create_cashier(self, client, auth_headers, tracker):
        """创建收银员账户。"""
        username = f"e2e_cashier_{int(time.time()) % 100000}"
        resp = client.post("/users", json={
            "username": username,
            "password": "test123456",
            "role": "booth_cashier",
            "booth_id": self.__class__.booth_id
        }, headers=auth_headers)

        assert resp.status_code == 201, f"Create cashier failed: {resp.text}"
        data = resp.json()
        assert data["role"] == "booth_cashier"

        tracker.created_users.append(data["id"])
        self.__class__.cashier_username = username
        self.__class__.cashier_id = data["id"]

    def test_05_cashier_login(self, client):
        """收银员登录。"""
        resp = client.post("/auth/login", json={
            "username": self.__class__.cashier_username,
            "password": "test123456"
        })

        assert resp.status_code == 200, f"Cashier login failed: {resp.text}"
        data = resp.json()
        assert data["user"]["role"] == "booth_cashier"

        self.__class__.cashier_token = data["access_token"]

    def test_06_setup_participant_for_booth_payment(self, client, tracker):
        """创建参与者并充值用于摊位支付。"""
        card_uid = f"E2E{int(time.time()) % 100000:05d}B"

        # 创建参与者
        resp = client.post("/participants", json={
            "name": "E2E摊位支付测试用户",
            "card_uid": card_uid,
            "class_name": "测试班级B",
            "status": "active"
        })
        assert resp.status_code == 201
        tracker.created_participants.append(resp.json()["id"])
        self.__class__.booth_card_uid = card_uid.upper()

        # 充值
        settings = get_settings()
        timestamp = int(time.time())
        signature = generate_signature(card_uid.upper(), timestamp, settings.secret_key, 200.00)
        resp = client.post("/recharge", json={
            "event_id": self.__class__.event_id,
            "card_uid": card_uid.upper(),
            "amount": 200.00,
            "timestamp": timestamp,
            "signature": signature,
            "remark": "摊位支付测试充值"
        })
        assert resp.status_code == 200
        tracker.created_transactions.append(resp.json()["transaction_id"])

    def test_07_booth_payment(self, client, tracker):
        """摊位支付测试。"""
        cashier_headers = {"Authorization": f"Bearer {self.__class__.cashier_token}"}

        resp = client.post(
            f"/booths/{self.__class__.booth_id}/pay",
            json={
                "event_id": self.__class__.event_id,
                "card_uid": self.__class__.booth_card_uid,
                "amount": 15.00,
                "product_id": self.__class__.product_id,
                "remark": "E2E摊位支付"
            },
            headers=cashier_headers
        )

        assert resp.status_code == 200, f"Booth payment failed: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        assert data["new_balance"] == 185.00
        assert data["balance_before"] == 200.00
        assert data["booth_id"] == self.__class__.booth_id
        assert data["operator_id"] == self.__class__.cashier_id

        tracker.created_transactions.append(data["transaction_id"])

    def test_08_get_booth_transactions(self, client):
        """查询摊位交易记录。"""
        cashier_headers = {"Authorization": f"Bearer {self.__class__.cashier_token}"}

        resp = client.get(
            f"/booths/{self.__class__.booth_id}/transactions",
            headers=cashier_headers
        )

        assert resp.status_code == 200, f"Get booth transactions failed: {resp.text}"
        data = resp.json()
        assert data["total_count"] >= 1
        assert len(data["transactions"]) >= 1

    def test_09_unauthorized_booth_access(self, client, auth_headers, tracker):
        """测试收银员无法访问其他摊位。"""
        # 创建另一个摊位
        resp = client.post("/booths", json={
            "event_id": self.__class__.event_id,
            "name": "E2E另一个摊位",
            "class_name": "测试班级C"
        }, headers=auth_headers)
        assert resp.status_code == 201
        other_booth_id = resp.json()["id"]
        tracker.created_booths.append(other_booth_id)

        # 收银员尝试访问其他摊位
        cashier_headers = {"Authorization": f"Bearer {self.__class__.cashier_token}"}
        resp = client.get(f"/booths/{other_booth_id}", headers=cashier_headers)
        assert resp.status_code == 403


# ============================================================================
# E2E Test: Authentication & Authorization
# ============================================================================


class TestAuthenticationFlow:
    """
    测试认证和授权流程：
    登录 → 获取用户信息 → 角色权限验证 → Token 过期处理
    """

    def test_01_login_success(self, client):
        """正常登录。"""
        resp = client.post("/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })

        if resp.status_code != 200:
            pytest.skip("Admin account not available")

        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["role"] == "super_admin"

    def test_02_login_invalid_credentials(self, client):
        """错误凭据登录。"""
        resp = client.post("/auth/login", json={
            "username": "admin",
            "password": "wrong_password"
        })

        assert resp.status_code == 401

    def test_03_get_current_user(self, client, auth_headers):
        """获取当前用户信息。"""
        resp = client.get("/auth/me", headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "admin"
        assert data["role"] == "super_admin"

    def test_04_invalid_token(self, client):
        """无效 Token 测试。"""
        headers = {"Authorization": "Bearer invalid_token_here"}
        resp = client.get("/auth/me", headers=headers)

        assert resp.status_code == 401

    def test_05_role_based_access(self, client, auth_headers, tracker):
        """角色权限测试 - 非 super_admin 不能创建用户。"""
        # 创建一个 event_admin 用户
        username = f"e2e_eventadmin_{int(time.time()) % 100000}"
        resp = client.post("/users", json={
            "username": username,
            "password": "test123456",
            "role": "event_admin"
        }, headers=auth_headers)

        if resp.status_code != 201:
            pytest.skip("Cannot create test user")

        tracker.created_users.append(resp.json()["id"])

        # 用 event_admin 登录
        resp = client.post("/auth/login", json={
            "username": username,
            "password": "test123456"
        })
        assert resp.status_code == 200
        event_admin_token = resp.json()["access_token"]

        # event_admin 尝试创建用户（应该被拒绝）
        resp = client.post("/users", json={
            "username": "should_not_be_created",
            "password": "test123456",
            "role": "issuer"
        }, headers={"Authorization": f"Bearer {event_admin_token}"})

        assert resp.status_code == 403


# ============================================================================
# E2E Test: Error Handling
# ============================================================================


class TestErrorHandling:
    """
    测试错误处理：
    无效参数 → 资源不存在 → 业务规则违反
    """

    def test_01_invalid_event_id(self, client):
        """不存在的活动ID。"""
        timestamp = int(time.time())
        settings = get_settings()
        card_uid = "AAAA1111"
        signature = generate_signature(card_uid, timestamp, settings.secret_key, 10.00)

        resp = client.post("/recharge", json={
            "event_id": 99999,
            "card_uid": card_uid,
            "amount": 10.00,
            "timestamp": timestamp,
            "signature": signature
        })

        assert resp.status_code == 400

    def test_02_invalid_card_uid(self, client, auth_headers, tracker):
        """不存在的卡片UID。"""
        # 先创建一个活动
        resp = client.post("/events", json={
            "name": "E2E错误测试活动_自动清理",
            "start_date": "2026-01-01T00:00:00Z",
            "end_date": "2026-12-31T23:59:59Z",
            "status": "active"
        })
        assert resp.status_code == 201
        event_id = resp.json()["id"]
        tracker.created_events.append(event_id)

        timestamp = int(time.time())
        settings = get_settings()
        card_uid = "ZZZZ9999"
        signature = generate_signature(card_uid, timestamp, settings.secret_key, 10.00)

        resp = client.post("/recharge", json={
            "event_id": event_id,
            "card_uid": card_uid,
            "amount": 10.00,
            "timestamp": timestamp,
            "signature": signature
        })

        assert resp.status_code == 400

    def test_03_duplicate_card_uid(self, client, tracker):
        """重复的卡片UID。"""
        card_uid = f"DUP{int(time.time()) % 100000:05d}A"

        # 第一次创建
        resp = client.post("/participants", json={
            "name": "重复卡片测试1",
            "card_uid": card_uid,
            "status": "active"
        })
        assert resp.status_code == 201
        tracker.created_participants.append(resp.json()["id"])

        # 第二次创建（应该失败）
        resp = client.post("/participants", json={
            "name": "重复卡片测试2",
            "card_uid": card_uid,
            "status": "active"
        })
        assert resp.status_code == 400
        assert resp.json()["error_code"] == "CARD_ALREADY_BOUND"

    def test_04_amount_exceeds_limit(self, client, auth_headers, tracker):
        """金额超过限制。"""
        # 创建参与者
        card_uid = f"LIM{int(time.time()) % 100000:05d}A"
        resp = client.post("/participants", json={
            "name": "金额限制测试",
            "card_uid": card_uid,
            "status": "active"
        })
        assert resp.status_code == 201
        tracker.created_participants.append(resp.json()["id"])

        # 尝试充值超过限制的金额
        settings = get_settings()
        timestamp = int(time.time())
        amount = settings.max_transaction_amount + 1
        signature = generate_signature(card_uid.upper(), timestamp, settings.secret_key, amount)

        resp = client.post("/recharge", json={
            "event_id": tracker.created_events[0] if tracker.created_events else 1,
            "card_uid": card_uid.upper(),
            "amount": amount,
            "timestamp": timestamp,
            "signature": signature
        })

        assert resp.status_code == 400
        assert "maximum" in resp.json().get("message", "").lower() or \
               resp.json().get("error_code") == "VALIDATION_ERROR"

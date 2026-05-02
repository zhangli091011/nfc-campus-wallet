"""
Demo Setup Script for NFC Campus Event System.

自动创建演示数据的脚本。
"""

import requests
import json
from datetime import datetime, timedelta
import sys

# 配置
BASE_URL = "http://localhost:8000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


class DemoSetup:
    """演示数据设置类"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.token = None
        self.event_id = None
        self.booth_ids = []
        self.product_ids = []
        self.participant_ids = []
        self.cashier_tokens = []
    
    def login(self, username: str, password: str) -> str:
        """登录并获取 token"""
        print(f"🔐 登录用户: {username}")
        
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password}
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data["access_token"]
            print(f"✅ 登录成功")
            return token
        else:
            print(f"❌ 登录失败: {response.text}")
            sys.exit(1)
    
    def register_admin(self):
        """注册管理员账户"""
        print(f"\n👤 注册管理员账户: {ADMIN_USERNAME}")
        
        response = requests.post(
            f"{self.base_url}/auth/register",
            json={
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD,
                "role": "super_admin"
            }
        )
        
        if response.status_code in [200, 201]:
            print(f"✅ 管理员账户创建成功")
        elif response.status_code == 400 and "already exists" in response.text:
            print(f"ℹ️  管理员账户已存在")
        else:
            print(f"❌ 创建失败: {response.text}")
            sys.exit(1)
    
    def create_event(self):
        """创建活动"""
        print(f"\n🎉 创建活动")
        
        start_time = datetime.now()
        end_time = start_time + timedelta(days=3)
        
        response = requests.post(
            f"{self.base_url}/events",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "name": "2024春季校园美食节",
                "start_time": start_time.isoformat() + "Z",
                "end_time": end_time.isoformat() + "Z",
                "status": "active",
                "recharge_enabled": True,
                "consume_enabled": True,
                "expire_rule": "event_end"
            }
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            self.event_id = data["id"]
            print(f"✅ 活动创建成功: ID={self.event_id}")
        else:
            print(f"❌ 创建失败: {response.text}")
            sys.exit(1)
    
    def create_booths(self):
        """创建摊位"""
        print(f"\n🏪 创建摊位")
        
        booths = [
            {"name": "美食天地", "class_name": "高一(1)班"},
            {"name": "清凉饮品站", "class_name": "高一(2)班"},
            {"name": "甜蜜时光", "class_name": "高一(3)班"}
        ]
        
        for booth in booths:
            response = requests.post(
                f"{self.base_url}/booths",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "event_id": self.event_id,
                    "name": booth["name"],
                    "class_name": booth["class_name"],
                    "status": "active"
                }
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.booth_ids.append(data["id"])
                print(f"✅ 摊位创建成功: {booth['name']} (ID={data['id']})")
            else:
                print(f"❌ 创建失败: {response.text}")
    
    def create_products(self):
        """创建商品"""
        print(f"\n🍔 创建商品")
        
        products = [
            # 美食天地
            {"booth_id": 0, "name": "烤肠", "price": 5.00, "cost": 2.50, "stock": 100},
            {"booth_id": 0, "name": "炸鸡翅", "price": 8.00, "cost": 4.00, "stock": 80},
            # 清凉饮品站
            {"booth_id": 1, "name": "珍珠奶茶", "price": 10.00, "cost": 4.00, "stock": 120},
            {"booth_id": 1, "name": "鲜榨果汁", "price": 12.00, "cost": 5.00, "stock": 100},
            # 甜蜜时光
            {"booth_id": 2, "name": "小蛋糕", "price": 15.00, "cost": 6.00, "stock": 60},
            {"booth_id": 2, "name": "冰淇淋", "price": 8.00, "cost": 3.00, "stock": 100}
        ]
        
        for product in products:
            booth_id = self.booth_ids[product["booth_id"]]
            
            response = requests.post(
                f"{self.base_url}/products",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "booth_id": booth_id,
                    "name": product["name"],
                    "price": product["price"],
                    "cost": product["cost"],
                    "stock": product["stock"],
                    "status": "available"
                }
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.product_ids.append(data["id"])
                print(f"✅ 商品创建成功: {product['name']} (ID={data['id']})")
            else:
                print(f"❌ 创建失败: {response.text}")
    
    def create_participants(self):
        """创建参与者"""
        print(f"\n👨‍🎓 创建参与者")
        
        participants = [
            {"name": "张三", "student_id": "2024001", "class_name": "高二(1)班", "card_uid": "A1B2C3D4"},
            {"name": "李四", "student_id": "2024002", "class_name": "高二(2)班", "card_uid": "E5F6G7H8"},
            {"name": "王五", "student_id": "2024003", "class_name": "高二(3)班", "card_uid": "I9J0K1L2"}
        ]
        
        for participant in participants:
            # 创建参与者
            response = requests.post(
                f"{self.base_url}/participants",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "name": participant["name"],
                    "student_id": participant["student_id"],
                    "class_name": participant["class_name"],
                    "phone": f"138001380{len(self.participant_ids):02d}"
                }
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                participant_id = data["id"]
                self.participant_ids.append(participant_id)
                print(f"✅ 参与者创建成功: {participant['name']} (ID={participant_id})")
                
                # 绑定卡片
                response = requests.post(
                    f"{self.base_url}/participants/{participant_id}/bind-card",
                    headers={"Authorization": f"Bearer {self.token}"},
                    json={"card_uid": participant["card_uid"]}
                )
                
                if response.status_code in [200, 201]:
                    print(f"✅ 卡片绑定成功: {participant['card_uid']}")
                else:
                    print(f"❌ 卡片绑定失败: {response.text}")
            else:
                print(f"❌ 创建失败: {response.text}")
    
    def issue_quotas(self):
        """发放活动额度"""
        print(f"\n💰 发放活动额度")
        
        card_uids = ["A1B2C3D4", "E5F6G7H8", "I9J0K1L2"]
        
        for card_uid in card_uids:
            response = requests.post(
                f"{self.base_url}/recharge",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "event_id": self.event_id,
                    "card_uid": card_uid,
                    "amount": 100.00,
                    "remark": "活动初始额度"
                }
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ 额度发放成功: {card_uid} -> 100.00 元")
            else:
                print(f"❌ 发放失败: {response.text}")
    
    def create_cashiers(self):
        """创建收银员"""
        print(f"\n👨‍💼 创建收银员")
        
        for i, booth_id in enumerate(self.booth_ids, start=1):
            username = f"cashier{i}"
            password = "cashier123"
            
            response = requests.post(
                f"{self.base_url}/auth/register",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "username": username,
                    "password": password,
                    "role": "booth_cashier",
                    "booth_id": booth_id
                }
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ 收银员创建成功: {username} (摊位ID={booth_id})")
                
                # 登录收银员获取 token
                cashier_token = self.login(username, password)
                self.cashier_tokens.append(cashier_token)
            elif response.status_code == 400 and "already exists" in response.text:
                print(f"ℹ️  收银员已存在: {username}")
                # 登录获取 token
                cashier_token = self.login(username, password)
                self.cashier_tokens.append(cashier_token)
            else:
                print(f"❌ 创建失败: {response.text}")
    
    def simulate_transactions(self):
        """模拟交易"""
        print(f"\n💳 模拟交易")
        
        transactions = [
            # 张三在美食天地消费
            {"cashier_idx": 0, "card_uid": "A1B2C3D4", "booth_idx": 0, "product_idx": 0, "amount": 5.00, "remark": "购买烤肠"},
            {"cashier_idx": 0, "card_uid": "A1B2C3D4", "booth_idx": 0, "product_idx": 1, "amount": 8.00, "remark": "购买炸鸡翅"},
            # 李四在清凉饮品站消费
            {"cashier_idx": 1, "card_uid": "E5F6G7H8", "booth_idx": 1, "product_idx": 2, "amount": 10.00, "remark": "购买珍珠奶茶"},
            # 王五在甜蜜时光消费
            {"cashier_idx": 2, "card_uid": "I9J0K1L2", "booth_idx": 2, "product_idx": 4, "amount": 15.00, "remark": "购买小蛋糕"},
            {"cashier_idx": 2, "card_uid": "I9J0K1L2", "booth_idx": 2, "product_idx": 5, "amount": 8.00, "remark": "购买冰淇淋"}
        ]
        
        for txn in transactions:
            response = requests.post(
                f"{self.base_url}/payment",
                headers={"Authorization": f"Bearer {self.cashier_tokens[txn['cashier_idx']]}"},
                json={
                    "event_id": self.event_id,
                    "card_uid": txn["card_uid"],
                    "amount": txn["amount"],
                    "booth_id": self.booth_ids[txn["booth_idx"]],
                    "product_id": self.product_ids[txn["product_idx"]],
                    "remark": txn["remark"]
                }
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ 交易成功: {txn['remark']} ({txn['amount']} 元)")
            else:
                print(f"❌ 交易失败: {response.text}")
    
    def run(self):
        """运行完整的演示设置"""
        print("=" * 60)
        print("NFC Campus Event System - Demo Setup")
        print("=" * 60)
        
        # 1. 注册管理员
        self.register_admin()
        
        # 2. 登录管理员
        self.token = self.login(ADMIN_USERNAME, ADMIN_PASSWORD)
        
        # 3. 创建活动
        self.create_event()
        
        # 4. 创建摊位
        self.create_booths()
        
        # 5. 创建商品
        self.create_products()
        
        # 6. 创建参与者
        self.create_participants()
        
        # 7. 发放额度
        self.issue_quotas()
        
        # 8. 创建收银员
        self.create_cashiers()
        
        # 9. 模拟交易
        self.simulate_transactions()
        
        print("\n" + "=" * 60)
        print("✅ 演示数据设置完成！")
        print("=" * 60)
        print(f"\n📊 数据摘要:")
        print(f"  - 活动ID: {self.event_id}")
        print(f"  - 摊位数量: {len(self.booth_ids)}")
        print(f"  - 商品数量: {len(self.product_ids)}")
        print(f"  - 参与者数量: {len(self.participant_ids)}")
        print(f"\n🔑 登录信息:")
        print(f"  - 管理员: {ADMIN_USERNAME} / {ADMIN_PASSWORD}")
        print(f"  - 收银员1: cashier1 / cashier123")
        print(f"  - 收银员2: cashier2 / cashier123")
        print(f"  - 收银员3: cashier3 / cashier123")
        print(f"\n🌐 访问地址:")
        print(f"  - API文档: {self.base_url}/docs")
        print(f"  - 健康检查: {self.base_url}/health")
        print("\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup demo data for NFC Campus Event System")
    parser.add_argument(
        "--url",
        default=BASE_URL,
        help=f"Backend URL (default: {BASE_URL})"
    )
    
    args = parser.parse_args()
    
    demo = DemoSetup(args.url)
    demo.run()

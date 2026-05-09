#!/usr/bin/env python3
"""
生成演示用测试数据
Generate demo data for NFC Campus Wallet System
"""

import sys
import os
import random
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import bcrypt

# 添加项目路径
sys.path.insert(0, '.')

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

from core.config import get_settings
from models.event import Event
from models.participant import Participant
from models.account import Account
from models.booth import Booth
from models.product import Product
from models.user import User
from models.transaction import Transaction
from core.database import Base


def hash_password(password: str) -> str:
    """生成密码哈希"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def generate_demo_data():
    """生成演示数据"""
    
    # 加载配置
    from core.config import load_settings
    load_settings()
    settings = get_settings()
    
    # 创建数据库连接
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("NFC Campus Wallet - 生成演示数据")
        print("=" * 60)
        
        # 检查是否已有数据
        existing_event = db.query(Event).filter(Event.name == "2026春季校园美食节").first()
        if existing_event:
            print("\n⚠️  检测到已存在的演示数据")
            print(f"   活动: {existing_event.name} (ID: {existing_event.id})")
            
            response = input("\n是否清除现有数据并重新生成? (y/N): ").strip().lower()
            if response != 'y':
                print("\n✓ 保留现有数据，退出")
                return True
            
            print("\n🗑️  清除现有数据...")
            # 删除相关数据（按依赖顺序）
            db.query(Transaction).filter(Transaction.event_id == existing_event.id).delete()
            db.query(Product).filter(Product.booth_id.in_(
                db.query(Booth.id).filter(Booth.event_id == existing_event.id)
            )).delete(synchronize_session=False)
            
            # 删除用户（收银员和充值员）
            db.query(User).filter(User.booth_id.in_(
                db.query(Booth.id).filter(Booth.event_id == existing_event.id)
            )).delete(synchronize_session=False)
            db.query(User).filter(User.username.in_([
                'issuer1', 'booth1_cashier', 'booth2_cashier', 'booth3_cashier',
                'booth4_cashier', 'booth5_cashier', 'booth6_cashier', 'booth7_cashier', 'booth8_cashier'
            ])).delete(synchronize_session=False)
            
            db.query(Account).filter(Account.event_id == existing_event.id).delete()
            db.query(Booth).filter(Booth.event_id == existing_event.id).delete()
            db.query(Participant).filter(Participant.card_uid.like('BOOTH_%')).delete()
            db.query(Participant).filter(Participant.card_uid.in_([
                'A1B2C3D4', 'E5F6G7H8', 'I9J0K1L2', 'M3N4O5P6', 'Q7R8S9T0',
                'U1V2W3X4', 'Y5Z6A7B8', 'C9D0E1F2', 'G3H4I5J6', 'K7L8M9N0'
            ])).delete(synchronize_session=False)
            db.query(Event).filter(Event.id == existing_event.id).delete()
            db.commit()
            print("✓ 清除完成")
        
        # 1. 创建活动
        print("\n📅 创建活动...")
        event = Event(
            name="2026春季校园美食节",
            start_date=datetime(2026, 5, 1, 0, 0, 0),
            end_date=datetime(2026, 5, 31, 23, 59, 59),
            status="active",
            allow_recharge=True,
            allow_payment=True
        )
        db.add(event)
        db.flush()
        print(f"✓ 创建活动: {event.name} (ID: {event.id})")
        
        # 2. 创建参与者（学生）
        print("\n👥 创建参与者...")
        students_data = [
            ("张三", "A1B2C3D4", "高一(1)班", "2024001"),
            ("李四", "E5F6G7H8", "高一(2)班", "2024002"),
            ("王五", "I9J0K1L2", "高二(1)班", "2023001"),
            ("赵六", "M3N4O5P6", "高二(2)班", "2023002"),
            ("钱七", "Q7R8S9T0", "高三(1)班", "2022001"),
            ("孙八", "U1V2W3X4", "高一(3)班", "2024003"),
            ("周九", "Y5Z6A7B8", "高二(3)班", "2023003"),
            ("吴十", "C9D0E1F2", "高三(2)班", "2022002"),
            ("郑十一", "G3H4I5J6", "高一(4)班", "2024004"),
            ("王十二", "K7L8M9N0", "高二(4)班", "2023004"),
        ]
        
        students = []
        for name, card_uid, class_name, student_no in students_data:
            student = Participant(
                name=name,
                card_uid=card_uid,
                class_name=class_name,
                student_no=student_no,
                participant_type="person",
                status="active"
            )
            db.add(student)
            students.append(student)
        
        db.flush()
        print(f"✓ 创建 {len(students)} 个学生参与者")
        
        # 3. 为参与者创建账户并充值
        print("\n💰 创建账户...")
        initial_balances = [10000, 15000, 20000, 12000, 18000, 25000, 8000, 30000, 5000, 22000]
        for i, student in enumerate(students):
            account = Account(
                participant_id=student.id,
                event_id=event.id,
                balance=initial_balances[i]
            )
            db.add(account)
        
        db.flush()
        print(f"✓ 创建 {len(students)} 个账户，余额范围: ¥50 - ¥300")
        
        # 4. 创建摊位
        print("\n🏪 创建摊位...")
        booths_data = [
            ("美味奶茶铺", "高一(1)班"),
            ("特色小吃摊", "高一(2)班"),
            ("创意甜品站", "高二(1)班"),
            ("健康果汁吧", "高二(2)班"),
            ("传统糕点屋", "高三(1)班"),
            ("异国风味馆", "高一(3)班"),
            ("烧烤天地", "高二(3)班"),
            ("冰淇淋乐园", "高三(2)班"),
        ]
        
        booths = []
        for name, class_name in booths_data:
            booth = Booth(
                event_id=event.id,
                name=name,
                class_name=class_name,
                status="active"
            )
            db.add(booth)
            booths.append(booth)
        
        db.flush()
        print(f"✓ 创建 {len(booths)} 个摊位")
        
        # 5. 为每个摊位创建收款账户
        print("\n💳 创建摊位收款账户...")
        for booth in booths:
            # 创建收款参与者
            collection_participant = Participant(
                name=f"【收款】{booth.name}",
                card_uid=f"BOOTH_{booth.id}",
                participant_type="booth_collection",
                status="active"
            )
            db.add(collection_participant)
            db.flush()
            
            # 创建收款账户
            collection_account = Account(
                participant_id=collection_participant.id,
                event_id=event.id,
                balance=0
            )
            db.add(collection_account)
            
            # 关联摊位和收款账户
            booth.collection_participant_id = collection_participant.id
        
        db.flush()
        print(f"✓ 为 {len(booths)} 个摊位创建收款账户")
        
        # 6. 创建商品
        print("\n🍔 创建商品...")
        products_data = {
            "美味奶茶铺": [
                ("珍珠奶茶", 1200, 600, 50),
                ("芝士奶盖", 1500, 700, 30),
                ("水果茶", 1000, 500, 40),
                ("布丁奶茶", 1300, 650, 35),
            ],
            "特色小吃摊": [
                ("章鱼小丸子", 800, 400, 100),
                ("臭豆腐", 1000, 500, 50),
                ("烤串拼盘", 1500, 800, 30),
                ("煎饼果子", 600, 300, 80),
            ],
            "创意甜品站": [
                ("芒果班戟", 1800, 900, 20),
                ("提拉米苏", 2000, 1000, 15),
                ("抹茶蛋糕", 1600, 800, 25),
                ("草莓慕斯", 1700, 850, 18),
            ],
            "健康果汁吧": [
                ("鲜榨橙汁", 1200, 600, 50),
                ("西瓜汁", 1000, 500, 40),
                ("混合果汁", 1500, 700, 30),
                ("芒果冰沙", 1400, 700, 35),
            ],
            "传统糕点屋": [
                ("绿豆糕", 600, 300, 100),
                ("桂花糕", 800, 400, 80),
                ("凤梨酥", 1000, 500, 60),
                ("蛋黄酥", 1200, 600, 50),
            ],
            "异国风味馆": [
                ("意大利披萨", 2500, 1200, 20),
                ("日式寿司", 2000, 1000, 25),
                ("韩式炸鸡", 1800, 900, 30),
                ("墨西哥卷饼", 1500, 750, 35),
            ],
            "烧烤天地": [
                ("羊肉串", 500, 250, 200),
                ("鸡翅", 800, 400, 100),
                ("烤玉米", 600, 300, 80),
                ("烤鱿鱼", 1200, 600, 50),
            ],
            "冰淇淋乐园": [
                ("香草冰淇淋", 800, 400, 60),
                ("巧克力圣代", 1200, 600, 40),
                ("水果冰淇淋", 1000, 500, 50),
                ("抹茶冰淇淋", 900, 450, 55),
            ],
        }
        
        total_products = 0
        for booth in booths:
            if booth.name in products_data:
                for name, price, cost_price, stock in products_data[booth.name]:
                    product = Product(
                        booth_id=booth.id,
                        name=name,
                        price=price,
                        cost_price=cost_price,
                        stock=stock,
                        enabled=True
                    )
                    db.add(product)
                    total_products += 1
        
        db.flush()
        print(f"✓ 创建 {total_products} 个商品")
        
        # 7. 创建用户（收银员）
        print("\n👤 创建用户...")
        cashier_password = hash_password("cashier123")
        
        users_created = 0
        for i, booth in enumerate(booths, 1):
            username = f"booth{i}_cashier"
            # 检查用户是否已存在
            existing_user = db.query(User).filter(User.username == username).first()
            if not existing_user:
                user = User(
                    username=username,
                    password_hash=cashier_password,
                    role="booth_cashier",
                    booth_id=booth.id,
                    status="active"
                )
                db.add(user)
                users_created += 1
        
        # 创建充值员
        existing_issuer = db.query(User).filter(User.username == "issuer1").first()
        if not existing_issuer:
            issuer = User(
                username="issuer1",
                password_hash=cashier_password,
                role="issuer",
                booth_id=None,
                status="active"
            )
            db.add(issuer)
            users_created += 1
        
        db.flush()
        print(f"✓ 创建 {users_created} 个用户（跳过已存在的用户）")
        
        # 8. 创建一些交易记录
        print("\n💸 创建交易记录...")
        
        # 获取所有账户和商品
        accounts = db.query(Account).join(Participant).filter(
            Participant.participant_type == "person",
            Account.event_id == event.id
        ).all()
        
        all_products = db.query(Product).all()
        
        # 生成随机交易
        transaction_count = 0
        for _ in range(30):  # 生成30笔交易
            account = random.choice(accounts)
            product = random.choice(all_products)
            booth = db.query(Booth).filter(Booth.id == product.booth_id).first()
            user = db.query(User).filter(User.booth_id == booth.id).first()
            
            if account.balance >= product.price:
                balance_before = account.balance
                balance_after = balance_before - product.price
                
                transaction = Transaction(
                    type="pay",
                    amount=product.price,
                    balance_before=balance_before,
                    balance_after=balance_after,
                    participant_id=account.participant_id,
                    event_id=event.id,
                    account_id=account.id,
                    booth_id=booth.id,
                    product_id=product.id,
                    operator_id=user.id if user else None,
                    remark=f"购买{product.name}"
                )
                db.add(transaction)
                
                # 更新账户余额
                account.balance = balance_after
                
                # 更新商品库存
                if product.stock > 0:
                    product.stock -= 1
                
                transaction_count += 1
        
        db.flush()
        print(f"✓ 创建 {transaction_count} 笔交易记录")
        
        # 提交所有更改
        db.commit()
        
        # 9. 显示摘要
        print("\n" + "=" * 60)
        print("✓ 演示数据生成完成！")
        print("=" * 60)
        
        print("\n📊 数据摘要:")
        print(f"  • 活动: {event.name}")
        print(f"  • 参与者: {len(students)} 人")
        print(f"  • 摊位: {len(booths)} 个")
        print(f"  • 商品: {total_products} 个")
        print(f"  • 用户: {len(booths) + 1} 个")
        print(f"  • 交易记录: {transaction_count} 笔")
        
        print("\n🔑 登录凭据:")
        print("  管理员:")
        print("    用户名: admin")
        print("    密码: admin123")
        print("\n  收银员 (任选一个):")
        print("    用户名: booth1_cashier ~ booth8_cashier")
        print("    密码: cashier123")
        print("\n  充值员:")
        print("    用户名: issuer1")
        print("    密码: cashier123")
        
        print("\n💳 测试卡片 (用于NFC刷卡):")
        for student in students[:5]:
            print(f"    {student.name}: {student.card_uid}")
        
        print("\n" + "=" * 60)
        print("现在可以使用系统进行测试了！")
        print("=" * 60)
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()
    
    return True


if __name__ == "__main__":
    success = generate_demo_data()
    sys.exit(0 if success else 1)

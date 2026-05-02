#!/usr/bin/env python3
"""
设置测试数据脚本

用于检查和创建测试活动、摊位等数据
"""

import sys
import os
from datetime import datetime, timedelta, timezone

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.orm import Session
from core.config import load_settings
from core.database import init_database, SessionLocal
from models.event import Event
from models.booth import Booth
from models.user import User
from core.security import get_password_hash


def setup_test_data():
    """设置测试数据"""
    print("=" * 60)
    print("设置测试数据")
    print("=" * 60)
    
    # Load configuration
    print("\n⚙️  加载配置...")
    try:
        load_settings()
        print("✅ 配置加载成功")
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False
    
    # Initialize database
    print("\n📦 初始化数据库...")
    try:
        init_database()
        print("✅ 数据库初始化成功")
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False
    
    # Create session
    db: Session = SessionLocal()
    
    try:
        # 1. 检查活动
        print("\n📋 检查活动...")
        active_event = db.query(Event).filter(Event.status == 'active').first()
        
        if active_event:
            print(f"✅ 找到活动活动: {active_event.name} (ID: {active_event.id})")
        else:
            print("⚠️  没有找到活跃活动，创建测试活动...")
            
            # 创建测试活动
            now = datetime.now(timezone.utc)
            event = Event(
                name="测试活动",
                start_time=now,
                end_time=now + timedelta(days=7),
                status='active',
                recharge_enabled=True,
                consume_enabled=True,
                expire_rule='event_end'
            )
            db.add(event)
            db.commit()
            db.refresh(event)
            active_event = event
            print(f"✅ 测试活动创建成功: {event.name} (ID: {event.id})")
        
        # 2. 检查摊位
        print("\n🏪 检查摊位...")
        booth = db.query(Booth).filter(
            Booth.event_id == active_event.id,
            Booth.status == 'active'
        ).first()
        
        if booth:
            print(f"✅ 找到活跃摊位: {booth.name} (ID: {booth.id})")
        else:
            print("⚠️  没有找到活跃摊位，创建测试摊位...")
            
            # 创建测试摊位
            booth = Booth(
                event_id=active_event.id,
                name="测试摊位",
                description="用于测试的摊位",
                status='active'
            )
            db.add(booth)
            db.commit()
            db.refresh(booth)
            print(f"✅ 测试摊位创建成功: {booth.name} (ID: {booth.id})")
        
        # 3. 检查用户
        print("\n👤 检查用户...")
        admin_user = db.query(User).filter(User.username == 'admin').first()
        
        if admin_user:
            print(f"✅ 找到管理员用户: {admin_user.username}")
        else:
            print("⚠️  没有找到管理员用户，创建测试用户...")
            
            # 创建管理员用户
            admin_user = User(
                username='admin',
                password_hash=get_password_hash('admin123'),
                role='admin',
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print(f"✅ 管理员用户创建成功: {admin_user.username} (密码: admin123)")
        
        # 4. 显示摘要
        print("\n" + "=" * 60)
        print("测试数据摘要")
        print("=" * 60)
        print(f"活动ID: {active_event.id}")
        print(f"活动名称: {active_event.name}")
        print(f"活动状态: {active_event.status}")
        print(f"摊位ID: {booth.id}")
        print(f"摊位名称: {booth.name}")
        print(f"摊位状态: {booth.status}")
        print(f"管理员用户: {admin_user.username}")
        print("=" * 60)
        
        print("\n✅ 测试数据设置完成！")
        print(f"\n💡 提示: 在安卓端登录时使用 booth_id={booth.id}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 设置测试数据失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    success = setup_test_data()
    sys.exit(0 if success else 1)

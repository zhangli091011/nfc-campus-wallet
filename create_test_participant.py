#!/usr/bin/env python3
"""
Create test participant for NFC wallet system.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import getpass

from models.participant import Participant


def create_test_participant():
    """Create a test participant."""
    print("=" * 60)
    print("Create Test Participant")
    print("=" * 60)
    
    # Get database credentials
    print("\n请输入数据库信息:")
    db_host = input("数据库主机 [localhost]: ").strip() or "localhost"
    db_port = input("数据库端口 [3306]: ").strip() or "3306"
    db_name = input("数据库名称 [nfc]: ").strip() or "nfc"
    db_user = input("数据库用户名 [nfc]: ").strip() or "nfc"
    db_password = getpass.getpass("数据库密码: ")
    
    # Create database connection
    database_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    print("\n📦 连接数据库...")
    try:
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        # Test connection
        db.execute("SELECT 1")
        print("✅ 数据库连接成功")
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        sys.exit(1)
    
    # Get participant info
    print("\n请输入参与者信息:")
    name = input("姓名: ").strip()
    card_uid = input("卡片UID [2BC8694C]: ").strip() or "2BC8694C"
    class_name = input("班级 [测试班级]: ").strip() or "测试班级"
    student_no = input("学号 [TEST001]: ").strip() or "TEST001"
    
    if not name:
        print("❌ 姓名不能为空")
        db.close()
        sys.exit(1)
    
    # Check if card already exists
    existing = db.query(Participant).filter(Participant.card_uid == card_uid).first()
    if existing:
        print(f"❌ 卡片 '{card_uid}' 已被绑定到参与者: {existing.name}")
        db.close()
        sys.exit(1)
    
    # Create participant
    print("\n🔨 创建参与者...")
    try:
        participant = Participant(
            name=name,
            card_uid=card_uid,
            class_name=class_name,
            student_no=student_no,
            status='active'
        )
        
        db.add(participant)
        db.commit()
        db.refresh(participant)
        
        print(f"\n✅ 参与者创建成功！")
        print(f"  - ID: {participant.id}")
        print(f"  - 姓名: {participant.name}")
        print(f"  - 卡片UID: {participant.card_uid}")
        print(f"  - 班级: {participant.class_name}")
        print(f"  - 学号: {participant.student_no}")
        print(f"  - 状态: {participant.status}")
        print(f"  - 创建时间: {participant.created_at}")
        
        print(f"\n📝 测试命令:")
        print(f"curl http://localhost:8001/participants/by-card/{card_uid}")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ 创建失败: {str(e)}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    create_test_participant()

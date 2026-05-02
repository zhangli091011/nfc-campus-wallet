"""
Simple script to create admin user directly.
"""

import sys
import os
import getpass
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from models.user import User
from core.security import hash_password


def create_admin():
    """Create admin user."""
    print("=" * 60)
    print("NFC Campus Event System - Create Admin User")
    print("=" * 60)
    
    # Get database credentials
    print("\n请输入数据库信息:")
    db_host = input("数据库主机 [localhost]: ").strip() or "localhost"
    db_port = input("数据库端口 [3306]: ").strip() or "3306"
    db_name = input("数据库名称 [nfc_wallet]: ").strip() or "nfc_wallet"
    db_user = input("数据库用户名: ").strip()
    db_password = getpass.getpass("数据库密码: ")
    
    if not db_user:
        print("❌ 数据库用户名不能为空")
        sys.exit(1)
    
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
    
    # Get admin credentials
    print("\n请输入管理员信息:")
    username = input("用户名: ").strip()
    
    if not username:
        print("❌ 用户名不能为空")
        sys.exit(1)
    
    # Check if user exists
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        print(f"❌ 用户名 '{username}' 已存在")
        db.close()
        sys.exit(1)
    
    password = getpass.getpass("密码: ")
    password_confirm = getpass.getpass("确认密码: ")
    
    if password != password_confirm:
        print("❌ 两次输入的密码不一致")
        db.close()
        sys.exit(1)
    
    if len(password) < 6:
        print("❌ 密码长度至少为 6 个字符")
        db.close()
        sys.exit(1)
    
    # Create admin user
    print("\n🔨 创建管理员账户...")
    try:
        hashed_password = hash_password(password)
        
        user = User(
            username=username,
            password_hash=hashed_password,
            role="super_admin",
            status="active"
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print(f"\n✅ 管理员账户创建成功！")
        print(f"  - 用户ID: {user.id}")
        print(f"  - 用户名: {user.username}")
        print(f"  - 角色: {user.role}")
        print(f"  - 状态: {user.status}")
        print(f"  - 创建时间: {user.created_at}")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ 创建失败: {str(e)}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    create_admin()

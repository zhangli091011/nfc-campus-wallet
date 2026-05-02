"""
Create Admin User Script.

创建管理员账户的脚本。
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from core.database import SessionLocal, init_database
from core.config import load_settings
from services.user_service import UserService
import getpass


def create_admin():
    """创建管理员账户"""
    print("=" * 60)
    print("NFC Campus Event System - Create Admin User")
    print("=" * 60)
    
    # 加载配置
    print("\n⚙️  加载配置...")
    try:
        load_settings()
        print("✅ 配置加载完成")
    except Exception as e:
        print(f"❌ 配置加载失败: {str(e)}")
        print("\n请确保 .env 文件存在并配置正确")
        sys.exit(1)
    
    # 初始化数据库
    print("\n📦 初始化数据库...")
    init_database()
    print("✅ 数据库初始化完成")
    
    # 获取用户输入
    print("\n请输入管理员信息:")
    username = input("用户名: ").strip()
    
    if not username:
        print("❌ 用户名不能为空")
        sys.exit(1)
    
    password = getpass.getpass("密码: ")
    password_confirm = getpass.getpass("确认密码: ")
    
    if password != password_confirm:
        print("❌ 两次输入的密码不一致")
        sys.exit(1)
    
    if len(password) < 6:
        print("❌ 密码长度至少为 6 个字符")
        sys.exit(1)
    
    # 创建管理员
    db: Session = SessionLocal()
    try:
        user_service = UserService(db)
        
        user = user_service.create_user(
            username=username,
            password=password,
            role="super_admin"
        )
        
        print(f"\n✅ 管理员账户创建成功！")
        print(f"  - 用户ID: {user.id}")
        print(f"  - 用户名: {user.username}")
        print(f"  - 角色: {user.role}")
        print(f"  - 创建时间: {user.created_at}")
        
    except Exception as e:
        print(f"\n❌ 创建失败: {str(e)}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    create_admin()

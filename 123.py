#!/usr/bin/env python3
"""
创建 Web Admin 管理员账号
Create Web Admin User Account
"""

import sys
import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加项目路径
sys.path.insert(0, '.')

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

from core.config import load_settings, get_settings
from models.user import User


def hash_password(password: str) -> str:
    """生成密码哈希"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def create_admin_user(username: str = "admin", password: str = "admin123", role: str = "super_admin"):
    """创建管理员账号"""
    
    # 加载配置
    load_settings()
    settings = get_settings()
    
    # 创建数据库连接
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("NFC Campus Wallet - 创建 Web Admin 管理员账号")
        print("=" * 60)
        
        # 检查用户是否已存在
        existing_user = db.query(User).filter(User.username == username).first()
        
        if existing_user:
            print(f"\n⚠️  用户 '{username}' 已存在")
            print(f"   角色: {existing_user.role}")
            print(f"   状态: {existing_user.status}")
            
            response = input("\n是否更新密码? (y/N): ").strip().lower()
            if response == 'y':
                # 更新密码
                existing_user.password_hash = hash_password(password)
                db.commit()
                print(f"\n✓ 密码已更新")
                print(f"   用户名: {username}")
                print(f"   新密码: {password}")
                return True
            else:
                print("\n✓ 保持现有账号不变")
                return True
        
        # 创建新用户
        print(f"\n👤 创建管理员账号...")
        print(f"   用户名: {username}")
        print(f"   密码: {password}")
        print(f"   角色: {role}")
        
        user = User(
            username=username,
            password_hash=hash_password(password),
            role=role,
            booth_id=None,
            status="active"
        )
        
        db.add(user)
        db.commit()
        
        print("\n" + "=" * 60)
        print("✓ 管理员账号创建成功！")
        print("=" * 60)
        
        print("\n🔑 登录凭据:")
        print(f"   用户名: {username}")
        print(f"   密码: {password}")
        print(f"   角色: {role}")
        
        print("\n📝 可用角色说明:")
        print("   • super_admin: 超级管理员（完全权限）")
        print("   • event_admin: 活动管理员（管理活动和摊位）")
        print("   • booth_cashier: 摊位收银员（仅限摊位操作）")
        print("   • issuer: 充值员（仅限充值操作）")
        
        print("\n" + "=" * 60)
        print("现在可以使用此账号登录 Web Admin 管理后台")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()


def create_multiple_users():
    """创建多个管理员账号"""
    
    print("=" * 60)
    print("NFC Campus Wallet - 批量创建管理员账号")
    print("=" * 60)
    
    users_to_create = [
        ("admin", "admin123", "super_admin", "超级管理员"),
        ("event_admin", "event123", "event_admin", "活动管理员"),
    ]
    
    # 加载配置
    load_settings()
    settings = get_settings()
    
    # 创建数据库连接
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for username, password, role, description in users_to_create:
            print(f"\n处理用户: {username} ({description})...")
            
            existing_user = db.query(User).filter(User.username == username).first()
            
            if existing_user:
                print(f"  ⚠️  用户已存在，跳过")
                skipped_count += 1
                continue
            
            user = User(
                username=username,
                password_hash=hash_password(password),
                role=role,
                booth_id=None,
                status="active"
            )
            
            db.add(user)
            created_count += 1
            print(f"  ✓ 创建成功")
        
        db.commit()
        
        print("\n" + "=" * 60)
        print("✓ 批量创建完成！")
        print("=" * 60)
        print(f"\n📊 统计:")
        print(f"   创建: {created_count} 个")
        print(f"   跳过: {skipped_count} 个")
        
        print("\n🔑 登录凭据:")
        for username, password, role, description in users_to_create:
            print(f"\n   {description}:")
            print(f"     用户名: {username}")
            print(f"     密码: {password}")
            print(f"     角色: {role}")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="创建 Web Admin 管理员账号")
    parser.add_argument("--username", "-u", default="admin", help="用户名 (默认: admin)")
    parser.add_argument("--password", "-p", default="admin123", help="密码 (默认: admin123)")
    parser.add_argument("--role", "-r", default="super_admin", 
                       choices=["super_admin", "event_admin", "booth_cashier", "issuer"],
                       help="角色 (默认: super_admin)")
    parser.add_argument("--batch", "-b", action="store_true", help="批量创建多个管理员账号")
    
    args = parser.parse_args()
    
    if args.batch:
        success = create_multiple_users()
    else:
        success = create_admin_user(args.username, args.password, args.role)
    
    sys.exit(0 if success else 1)

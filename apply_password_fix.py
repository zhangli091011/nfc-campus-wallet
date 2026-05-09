"""
应用密码修复脚本
"""

import sys
sys.path.insert(0, '.')

from sqlalchemy import create_engine, text
from core.config import load_settings, get_settings

def main():
    print("=" * 80)
    print("应用密码修复")
    print("=" * 80)
    print()
    
    # 加载配置
    load_settings()
    settings = get_settings()
    
    print("数据库连接信息:")
    print(f"  主机: {settings.database_host}")
    print(f"  端口: {settings.database_port}")
    print(f"  用户: {settings.database_user}")
    print(f"  数据库: {settings.database_name}")
    print()
    
    # 创建数据库连接
    engine = create_engine(settings.database_url)
    
    print("正在应用密码修复...")
    print()
    
    # 执行密码修复
    with engine.connect() as conn:
        # 更新 admin 用户密码 (密码: admin123)
        result = conn.execute(text("""
            UPDATE users 
            SET password_hash = '$2b$12$14BtTTqR5hA8SiGciAp89uvy.09EtoZnz7zt8cGTZDyezaYfMSPrq'
            WHERE username = 'admin'
        """))
        conn.commit()
        print(f"✓ 更新 admin 用户密码: {result.rowcount} 行")
        
        # 更新所有收银员和充值员密码 (密码: cashier123)
        result = conn.execute(text("""
            UPDATE users 
            SET password_hash = '$2b$12$8Juz3NGP7Emas/knJW6gxuZMAJKjdQ925q3toBZkcU1vxgb9i7Q3O'
            WHERE role IN ('booth_cashier', 'issuer', 'reviewer')
        """))
        conn.commit()
        print(f"✓ 更新收银员/充值员密码: {result.rowcount} 行")
        
        print()
        print("-" * 80)
        print("验证更新结果:")
        print()
        
        # 验证更新结果
        result = conn.execute(text("""
            SELECT 
                username,
                role,
                LEFT(password_hash, 20) AS password_hash_prefix,
                CASE 
                    WHEN username = 'admin' THEN 'admin123'
                    ELSE 'cashier123'
                END AS password
            FROM users
            ORDER BY role, username
        """))
        
        users = result.fetchall()
        for user in users:
            username, role, hash_prefix, password = user
            print(f"  {username:20s} | {role:15s} | 密码: {password}")
    
    print()
    print("=" * 80)
    print("✅ 密码修复成功！")
    print("=" * 80)
    print()
    print("更新后的登录凭据:")
    print()
    print("  管理员:")
    print("    用户名: admin")
    print("    密码: admin123")
    print()
    print("  收银员 (booth1_cashier ~ booth5_cashier):")
    print("    密码: cashier123")
    print()
    print("  充值员 (issuer1):")
    print("    密码: cashier123")
    print()

if __name__ == "__main__":
    main()

"""
Generate password hash for manual user creation.
"""

import sys
import getpass

# Add project root to path
sys.path.insert(0, ".")

from core.security import hash_password


def main():
    """Generate password hash."""
    print("=" * 60)
    print("Password Hash Generator")
    print("=" * 60)
    
    password = getpass.getpass("\n输入密码: ")
    
    if not password:
        print("❌ 密码不能为空")
        sys.exit(1)
    
    hashed = hash_password(password)
    
    print(f"\n✅ 密码哈希生成成功:")
    print(f"\n{hashed}")
    
    print(f"\n\n📋 SQL语句:")
    print(f"""
INSERT INTO users (username, hashed_password, role, is_active, created_at)
VALUES (
    'admin',
    '{hashed}',
    'super_admin',
    1,
    NOW()
);
""")


if __name__ == "__main__":
    main()

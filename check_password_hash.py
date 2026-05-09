"""
检查密码哈希是否正确
"""

import sys
sys.path.insert(0, ".")

from core.security import hash_password, verify_password

def main():
    print("=" * 80)
    print("检查密码哈希")
    print("=" * 80)
    
    # 检查 create_test_data.sql 中的哈希
    stored_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEiUM2"
    
    print(f"\n存储的哈希: {stored_hash}")
    print(f"哈希长度: {len(stored_hash)}")
    print()
    
    # 测试不同的密码
    test_passwords = ["cashier123", "admin123", "123456", "password", "admin"]
    
    print("测试密码:")
    for pwd in test_passwords:
        try:
            is_valid = verify_password(pwd, stored_hash)
            print(f"  {'✅' if is_valid else '❌'} {pwd:15s} - {'匹配' if is_valid else '不匹配'}")
        except Exception as e:
            print(f"  ❌ {pwd:15s} - 错误: {e}")
    
    print()
    print("-" * 80)
    print("生成新的密码哈希:")
    print()
    
    # 生成新的哈希
    for pwd in ["admin123", "cashier123"]:
        new_hash = hash_password(pwd)
        print(f"密码: {pwd}")
        print(f"哈希: {new_hash}")
        
        # 验证新生成的哈希
        is_valid = verify_password(pwd, new_hash)
        print(f"验证: {'✅ 成功' if is_valid else '❌ 失败'}")
        print()

if __name__ == "__main__":
    main()

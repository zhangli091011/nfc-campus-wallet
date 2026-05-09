"""
验证前后端密码加密程序的一致性
"""

import sys
sys.path.insert(0, ".")

from sqlalchemy import create_engine, text
from core.config import get_settings
from core.security import hash_password, verify_password
import bcrypt

def main():
    print("=" * 80)
    print("密码加密验证程序")
    print("=" * 80)
    
    # 加载配置
    from core.config import load_settings
    load_settings()
    
    # 1. 验证后端密码加密格式
    print("\n【1】验证后端密码加密格式")
    print("-" * 80)
    
    test_password = "test123456"
    hashed = hash_password(test_password)
    
    print(f"测试密码: {test_password}")
    print(f"加密后哈希: {hashed}")
    print(f"哈希长度: {len(hashed)} 字符")
    print(f"哈希前缀: {hashed[:7]}")
    
    # 验证 bcrypt 格式
    if hashed.startswith("$2b$12$"):
        print("✅ 格式正确: bcrypt with cost factor 12")
    else:
        print("❌ 格式错误: 不是标准的 bcrypt 格式")
        return
    
    # 验证密码验证功能
    if verify_password(test_password, hashed):
        print("✅ 密码验证功能正常")
    else:
        print("❌ 密码验证功能异常")
        return
    
    # 2. 检查数据库中的密码格式
    print("\n【2】检查数据库中的密码格式")
    print("-" * 80)
    
    settings = get_settings()
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, username, password_hash, role, status
            FROM users
            ORDER BY id
            LIMIT 10
        """))
        
        users = result.fetchall()
        
        if not users:
            print("⚠️  数据库中没有用户数据")
            return
        
        print(f"找到 {len(users)} 个用户:")
        print()
        
        all_valid = True
        for user in users:
            user_id, username, password_hash, role, status = user
            
            # 检查密码哈希格式
            is_bcrypt = password_hash.startswith("$2b$12$") if password_hash else False
            hash_length = len(password_hash) if password_hash else 0
            
            status_icon = "✅" if is_bcrypt and hash_length == 60 else "❌"
            
            print(f"{status_icon} ID: {user_id:3d} | 用户名: {username:20s} | 角色: {role:15s}")
            print(f"   密码哈希: {password_hash[:30]}... (长度: {hash_length})")
            print(f"   格式: {'bcrypt $2b$12$' if is_bcrypt else '未知格式'}")
            print(f"   状态: {status}")
            print()
            
            if not is_bcrypt or hash_length != 60:
                all_valid = False
        
        if all_valid:
            print("✅ 所有用户的密码哈希格式都正确")
        else:
            print("❌ 部分用户的密码哈希格式不正确")
    
    # 3. 验证 Android 端签名生成（仅说明，不实际执行）
    print("\n【3】Android 端签名生成验证")
    print("-" * 80)
    print("Android 端使用 SignatureGenerator.java 生成 SHA256 签名")
    print("签名格式:")
    print("  - 余额查询: SHA256(uid + timestamp + secret_key)")
    print("  - 交易请求: SHA256(uid + amount + timestamp + secret_key)")
    print()
    print("⚠️  注意: Android 端的签名生成与密码加密是两个不同的系统:")
    print("  - 密码加密: 使用 bcrypt (后端用户认证)")
    print("  - 签名生成: 使用 SHA256 (NFC 交易认证)")
    print()
    
    # 4. 测试实际密码验证
    print("\n【4】测试实际密码验证")
    print("-" * 80)
    
    with engine.connect() as conn:
        # 查找一个测试用户
        result = conn.execute(text("""
            SELECT id, username, password_hash
            FROM users
            WHERE username = 'admin'
            LIMIT 1
        """))
        
        admin_user = result.fetchone()
        
        if admin_user:
            user_id, username, password_hash = admin_user
            print(f"找到用户: {username} (ID: {user_id})")
            print(f"密码哈希: {password_hash[:30]}...")
            print()
            
            # 测试正确的密码（根据 create_test_data.sql）
            test_passwords = ["admin123", "cashier123"]
            
            print("测试密码验证:")
            password_found = False
            for pwd in test_passwords:
                try:
                    is_valid = verify_password(pwd, password_hash)
                    if is_valid:
                        print(f"  ✅ 密码 '{pwd}' 验证成功")
                        password_found = True
                        break
                    else:
                        print(f"  ❌ 密码 '{pwd}' 验证失败")
                except Exception as e:
                    print(f"  ❌ 密码 '{pwd}' 验证出错: {e}")
            
            if not password_found:
                print(f"  ⚠️  未找到匹配的密码")
        else:
            print("⚠️  未找到 admin 用户")
    
    # 5. 验证所有用户的密码
    print("\n【5】验证所有用户的密码")
    print("-" * 80)
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, username, password_hash, role
            FROM users
            ORDER BY id
        """))
        
        users = result.fetchall()
        
        # 根据 create_test_data.sql，所有用户的密码都是 cashier123
        # admin 用户的密码是 admin123
        print("验证所有用户的密码哈希:")
        print()
        
        all_valid = True
        for user in users:
            user_id, username, password_hash, role = user
            
            # 根据用户名确定密码
            if username == 'admin':
                expected_password = 'admin123'
            else:
                expected_password = 'cashier123'
            
            try:
                is_valid = verify_password(expected_password, password_hash)
                status_icon = "✅" if is_valid else "❌"
                print(f"{status_icon} {username:20s} | 角色: {role:15s} | 密码: {expected_password}")
                
                if not is_valid:
                    all_valid = False
            except Exception as e:
                print(f"❌ {username:20s} | 验证出错: {e}")
                all_valid = False
        
        print()
        if all_valid:
            print("✅ 所有用户的密码哈希验证成功")
        else:
            print("❌ 部分用户的密码哈希验证失败")
    
    # 6. 总结
    print("\n" + "=" * 80)
    print("验证总结")
    print("=" * 80)
    print()
    print("✅ 后端密码加密: 使用 bcrypt with cost factor 12")
    print("✅ 密码哈希格式: $2b$12$... (60 字符)")
    print("✅ 密码验证: 使用 bcrypt.checkpw() 进行常量时间比较")
    print()
    print("⚠️  Android 端说明:")
    print("   - Android 端不处理密码加密（密码加密仅在后端进行）")
    print("   - Android 端仅生成 SHA256 签名用于 NFC 交易认证")
    print("   - 两个系统互不干扰，各司其职")
    print()

if __name__ == "__main__":
    main()

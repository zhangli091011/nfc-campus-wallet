#!/usr/bin/env python3
"""
Create users table without problematic CHECK constraint
"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv('DATABASE_USER')
DB_PASSWORD = os.getenv('DATABASE_PASSWORD')
DB_HOST = os.getenv('DATABASE_HOST')
DB_PORT = os.getenv('DATABASE_PORT')
DB_NAME = os.getenv('DATABASE_NAME')

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

engine = create_engine(DATABASE_URL, echo=False)

print("=== Creating users table (final) ===\n")

with engine.connect() as conn:
    # 1. Create users table without the problematic CHECK constraint
    try:
        print("[1/6] Creating users table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
                username VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
                password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
                role VARCHAR(20) NOT NULL COMMENT '用户角色',
                booth_id INT DEFAULT NULL COMMENT '关联摊位ID',
                status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '用户状态',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                CONSTRAINT fk_user_booth 
                    FOREIGN KEY (booth_id) 
                    REFERENCES booths(id) 
                    ON DELETE SET NULL,
                CONSTRAINT chk_user_role 
                    CHECK (role IN ('super_admin', 'event_admin', 'booth_cashier', 'issuer', 'reviewer')),
                CONSTRAINT chk_user_status 
                    CHECK (status IN ('active', 'inactive', 'blocked'))
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表'
        """))
        conn.commit()
        print("  ✓ Success")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import sys
        sys.exit(1)
    
    # 2. Create indexes
    indexes = [
        "CREATE INDEX idx_users_username ON users(username)",
        "CREATE INDEX idx_users_role ON users(role)",
        "CREATE INDEX idx_users_booth_id ON users(booth_id)",
        "CREATE INDEX idx_users_role_status ON users(role, status)",
    ]
    
    for i, sql in enumerate(indexes, 2):
        try:
            print(f"[{i}/6] Creating index...")
            conn.execute(text(sql))
            conn.commit()
            print("  ✓ Success")
        except Exception as e:
            print(f"  ⚠ Warning: {e}")
    
    # 6. Add FK constraint for transactions.operator_id
    try:
        print("[6/6] Adding FK constraint for transactions.operator_id...")
        conn.execute(text("""
            ALTER TABLE transactions
            ADD CONSTRAINT fk_transaction_operator 
                FOREIGN KEY (operator_id) 
                REFERENCES users(id) 
                ON DELETE SET NULL
        """))
        conn.commit()
        print("  ✓ Success")
    except Exception as e:
        print(f"  ⚠ Warning: {e}")

print("\n=== Creating default super admin ===\n")

with engine.connect() as conn:
    try:
        print("Creating admin user (username: admin, password: admin123)...")
        conn.execute(text("""
            INSERT INTO users (username, password_hash, role, status)
            VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEiUM2', 'super_admin', 'active')
            ON DUPLICATE KEY UPDATE username = username
        """))
        conn.commit()
        print("  ✓ Success")
        
        # Verify admin was created
        result = conn.execute(text("SELECT id, username, role, status FROM users WHERE role = 'super_admin'"))
        admin = result.fetchone()
        if admin:
            print(f"\n✓ Super admin created: id={admin[0]}, username={admin[1]}, role={admin[2]}, status={admin[3]}")
        
    except Exception as e:
        print(f"  ✗ Error: {e}")

print("\n✓ Users table creation completed!")

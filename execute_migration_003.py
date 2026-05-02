#!/usr/bin/env python3
"""
Execute Migration 003 - Booth Management System
This script assumes migrations 001 and 002 have already been run.
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv('DATABASE_USER', 'nfc_wallet')
DB_PASSWORD = os.getenv('DATABASE_PASSWORD')
DB_HOST = os.getenv('DATABASE_HOST', 'localhost')
DB_PORT = os.getenv('DATABASE_PORT', '3306')
DB_NAME = os.getenv('DATABASE_NAME', 'nfc_wallet')

if not DB_PASSWORD:
    print("ERROR: DATABASE_PASSWORD not set in environment")
    sys.exit(1)

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

def check_prerequisites(engine):
    """Check if previous migrations have been run"""
    print("\n=== Checking Prerequisites ===")
    
    required_tables = ['events', 'participants', 'accounts']
    
    with engine.connect() as conn:
        result = conn.execute(text("SHOW TABLES"))
        existing_tables = [row[0] for row in result.fetchall()]
        
        missing_tables = [t for t in required_tables if t not in existing_tables]
        
        if missing_tables:
            print(f"✗ Missing required tables: {', '.join(missing_tables)}")
            print("\nPlease run migrations 001 and 002 first:")
            print("  - migrations/001_upgrade_to_ledger_mode.sql")
            print("  - migrations/002_upgrade_to_event_system.sql")
            return False
        
        print(f"✓ All prerequisite tables exist")
        for table in required_tables:
            count_result = conn.execute(text(f"SELECT COUNT(*) as cnt FROM {table}"))
            count = count_result.fetchone()[0]
            print(f"  - {table}: {count} rows")
    
    return True

def backup_database(engine):
    """Create a backup record before migration"""
    print("\n=== Creating Backup Record ===")
    
    backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    with engine.connect() as conn:
        result = conn.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result.fetchall()]
        
        print(f"Database state at {backup_timestamp}:")
        for table in tables:
            count_result = conn.execute(text(f"SELECT COUNT(*) as cnt FROM {table}"))
            count = count_result.fetchone()[0]
            print(f"  - {table}: {count} rows")
    
    print("\n⚠ For production, create a full backup using mysqldump")
    return True

def execute_migration_003(engine):
    """Execute migration 003 statements"""
    print("\n=== Executing Migration 003: Booth Management System ===\n")
    
    statements = [
        # 1. Create booths table
        ("""CREATE TABLE IF NOT EXISTS booths (
            id INT AUTO_INCREMENT PRIMARY KEY COMMENT '摊位ID',
            event_id INT NOT NULL COMMENT '活动ID',
            name VARCHAR(100) NOT NULL COMMENT '摊位名称',
            class_name VARCHAR(100) NOT NULL COMMENT '班级名称',
            status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '摊位状态',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            CONSTRAINT fk_booth_event 
                FOREIGN KEY (event_id) 
                REFERENCES events(id) 
                ON DELETE CASCADE,
            CONSTRAINT chk_booth_status 
                CHECK (status IN ('active', 'inactive', 'closed'))
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='摊位表'""", "Create booths table"),
        
        ("CREATE INDEX idx_booths_event_id ON booths(event_id)", "Create index on booths.event_id"),
        
        # 2. Create products table
        ("""CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY COMMENT '商品ID',
            booth_id INT NOT NULL COMMENT '摊位ID',
            name VARCHAR(100) NOT NULL COMMENT '商品名称',
            price INT NOT NULL COMMENT '售价（分）',
            cost_price INT DEFAULT NULL COMMENT '成本价（分）',
            stock INT DEFAULT NULL COMMENT '库存数量',
            enabled BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            CONSTRAINT fk_product_booth 
                FOREIGN KEY (booth_id) 
                REFERENCES booths(id) 
                ON DELETE CASCADE,
            CONSTRAINT chk_price_non_negative 
                CHECK (price >= 0),
            CONSTRAINT chk_cost_price_non_negative 
                CHECK (cost_price IS NULL OR cost_price >= 0),
            CONSTRAINT chk_stock_non_negative 
                CHECK (stock IS NULL OR stock >= 0)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='商品表'""", "Create products table"),
        
        ("CREATE INDEX idx_products_booth_id ON products(booth_id)", "Create index on products.booth_id"),
        
        # 3. Create users table
        ("""CREATE TABLE IF NOT EXISTS users (
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
                CHECK (status IN ('active', 'inactive', 'blocked')),
            CONSTRAINT chk_booth_cashier_has_booth 
                CHECK ((role = 'booth_cashier' AND booth_id IS NOT NULL) OR (role != 'booth_cashier'))
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表'""", "Create users table"),
        
        ("CREATE INDEX idx_users_username ON users(username)", "Create index on users.username"),
        ("CREATE INDEX idx_users_role ON users(role)", "Create index on users.role"),
        ("CREATE INDEX idx_users_booth_id ON users(booth_id)", "Create index on users.booth_id"),
        
        # 4. Enhance transactions table
        ("ALTER TABLE transactions ADD COLUMN booth_id INT DEFAULT NULL COMMENT '摊位ID'", "Add booth_id to transactions"),
        ("ALTER TABLE transactions ADD COLUMN product_id INT DEFAULT NULL COMMENT '商品ID'", "Add product_id to transactions"),
        ("ALTER TABLE transactions ADD COLUMN operator_id INT DEFAULT NULL COMMENT '操作员用户ID'", "Add operator_id to transactions"),
        
        # Add foreign keys
        ("""ALTER TABLE transactions
            ADD CONSTRAINT fk_transaction_booth 
                FOREIGN KEY (booth_id) 
                REFERENCES booths(id) 
                ON DELETE SET NULL""", "Add FK: transactions.booth_id"),
        
        ("""ALTER TABLE transactions
            ADD CONSTRAINT fk_transaction_product 
                FOREIGN KEY (product_id) 
                REFERENCES products(id) 
                ON DELETE SET NULL""", "Add FK: transactions.product_id"),
        
        ("""ALTER TABLE transactions
            ADD CONSTRAINT fk_transaction_operator 
                FOREIGN KEY (operator_id) 
                REFERENCES users(id) 
                ON DELETE SET NULL""", "Add FK: transactions.operator_id"),
        
        # Add indexes
        ("CREATE INDEX idx_transactions_booth_id ON transactions(booth_id)", "Create index on transactions.booth_id"),
        ("CREATE INDEX idx_transactions_product_id ON transactions(product_id)", "Create index on transactions.product_id"),
        ("CREATE INDEX idx_transactions_operator_id ON transactions(operator_id)", "Create index on transactions.operator_id"),
        
        # 5. Insert default super admin
        ("""INSERT INTO users (username, password_hash, role, status)
            VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEiUM2', 'super_admin', 'active')
            ON DUPLICATE KEY UPDATE username = username""", "Create default super admin"),
        
        # 6. Create composite indexes for optimization
        ("CREATE INDEX idx_transactions_booth_created ON transactions(booth_id, created_at)", "Create composite index: booth_id, created_at"),
        ("CREATE INDEX idx_transactions_product_created ON transactions(product_id, created_at)", "Create composite index: product_id, created_at"),
        ("CREATE INDEX idx_products_booth_enabled ON products(booth_id, enabled)", "Create composite index: booth_id, enabled"),
        ("CREATE INDEX idx_users_role_status ON users(role, status)", "Create composite index: role, status"),
    ]
    
    executed = 0
    warnings = 0
    failed = 0
    
    with engine.connect() as conn:
        for i, (statement, description) in enumerate(statements, 1):
            try:
                print(f"[{i}/{len(statements)}] {description}")
                conn.execute(text(statement))
                conn.commit()
                executed += 1
                print("  ✓ Success")
                
            except Exception as e:
                error_msg = str(e)
                # Check if it's a "already exists" or "duplicate" error
                if any(keyword in error_msg.lower() for keyword in ['already exists', 'duplicate']):
                    print(f"  ⚠ Warning: {error_msg}")
                    warnings += 1
                else:
                    print(f"  ✗ Error: {error_msg}")
                    failed += 1
    
    print(f"\n{'=' * 70}")
    print(f"Migration Summary:")
    print(f"  ✓ Executed: {executed}")
    print(f"  ⚠ Warnings: {warnings}")
    print(f"  ✗ Failed: {failed}")
    print('=' * 70)
    
    return failed == 0

def verify_migration(engine):
    """Verify that migration was successful"""
    print("\n=== Verifying Migration ===")
    
    checks = [
        ("Booths table exists", "SELECT COUNT(*) as cnt FROM booths"),
        ("Products table exists", "SELECT COUNT(*) as cnt FROM products"),
        ("Users table exists", "SELECT COUNT(*) as cnt FROM users"),
        ("Transactions has booth_id", "SHOW COLUMNS FROM transactions LIKE 'booth_id'"),
        ("Transactions has product_id", "SHOW COLUMNS FROM transactions LIKE 'product_id'"),
        ("Transactions has operator_id", "SHOW COLUMNS FROM transactions LIKE 'operator_id'"),
        ("Super admin exists", "SELECT id, username, role, status FROM users WHERE role = 'super_admin'"),
    ]
    
    all_passed = True
    
    with engine.connect() as conn:
        for description, query in checks:
            try:
                result = conn.execute(text(query))
                rows = result.fetchall()
                
                if rows:
                    if 'COUNT' in query:
                        print(f"✓ {description}: {rows[0][0]} records")
                    elif 'SHOW COLUMNS' in query:
                        print(f"✓ {description}: Column exists")
                    else:
                        print(f"✓ {description}:")
                        for row in rows:
                            print(f"    {row}")
                else:
                    print(f"✗ {description}: Failed")
                    all_passed = False
                    
            except Exception as e:
                print(f"✗ {description}: Error - {e}")
                all_passed = False
    
    return all_passed

def main():
    print("=" * 70)
    print("Migration 003: Booth Management System")
    print("=" * 70)
    
    # Create database engine
    try:
        print(f"\nConnecting to database: {DB_HOST}:{DB_PORT}/{DB_NAME}")
        engine = create_engine(DATABASE_URL, echo=False)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        print("✓ Database connection successful")
        
    except Exception as e:
        print(f"\n✗ ERROR: Failed to connect to database: {e}")
        sys.exit(1)
    
    # Check prerequisites
    if not check_prerequisites(engine):
        sys.exit(1)
    
    # Backup
    if not backup_database(engine):
        sys.exit(1)
    
    # Execute migration
    if not execute_migration_003(engine):
        print("\n✗ Migration failed. Please review errors above.")
        sys.exit(1)
    
    # Verify
    if not verify_migration(engine):
        print("\n⚠ Migration verification found issues.")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("✓ Migration 003 completed successfully!")
    print("=" * 70)
    print("\n🔐 Default Super Admin Account:")
    print("  Username: admin")
    print("  Password: admin123")
    print("\n⚠ IMPORTANT: Change the default admin password immediately!")
    print("=" * 70)

if __name__ == "__main__":
    main()

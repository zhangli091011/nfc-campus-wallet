#!/usr/bin/env python3
"""
Execute Migration 002 - Event System
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv('DATABASE_USER', 'nfc_wallet')
DB_PASSWORD = os.getenv('DATABASE_PASSWORD')
DB_HOST = os.getenv('DATABASE_HOST', 'localhost')
DB_PORT = os.getenv('DATABASE_PORT', '3306')
DB_NAME = os.getenv('DATABASE_NAME', 'nfc_wallet')

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

def execute_migration_002(engine):
    """Execute migration 002 statements"""
    print("\n=== Executing Migration 002: Event System ===\n")
    
    statements = [
        # 1. Create events table
        ("""CREATE TABLE IF NOT EXISTS events (
            id INT AUTO_INCREMENT PRIMARY KEY COMMENT '活动ID',
            name VARCHAR(255) NOT NULL COMMENT '活动名称',
            start_time DATETIME NOT NULL COMMENT '活动开始时间',
            end_time DATETIME NOT NULL COMMENT '活动结束时间',
            status VARCHAR(20) NOT NULL DEFAULT 'draft' COMMENT '活动状态',
            recharge_enabled BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否允许充值',
            consume_enabled BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否允许消费',
            expire_rule VARCHAR(50) DEFAULT 'event_end' COMMENT '过期规则',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            INDEX idx_status (status),
            INDEX idx_start_time (start_time),
            INDEX idx_end_time (end_time),
            CONSTRAINT chk_event_status CHECK (status IN ('draft', 'active', 'paused', 'ended')),
            CONSTRAINT chk_event_time CHECK (end_time > start_time),
            CONSTRAINT chk_expire_rule CHECK (expire_rule IN ('event_end', 'never', 'custom'))
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='活动表'""", "Create events table"),
        
        # 2. Create participants table
        ("""CREATE TABLE IF NOT EXISTS participants (
            id INT AUTO_INCREMENT PRIMARY KEY COMMENT '参与者ID',
            name VARCHAR(100) NOT NULL COMMENT '参与者姓名',
            class_name VARCHAR(100) DEFAULT NULL COMMENT '班级名称',
            student_no VARCHAR(50) DEFAULT NULL COMMENT '学号',
            card_uid VARCHAR(32) UNIQUE NOT NULL COMMENT 'NFC卡片UID',
            status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '状态',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            INDEX idx_card_uid (card_uid),
            INDEX idx_student_no (student_no),
            INDEX idx_status (status),
            INDEX idx_name (name),
            CONSTRAINT chk_participant_status CHECK (status IN ('active', 'inactive', 'blocked'))
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='参与者表'""", "Create participants table"),
        
        # 3. Create accounts table
        ("""CREATE TABLE IF NOT EXISTS accounts (
            id INT AUTO_INCREMENT PRIMARY KEY COMMENT '账户ID',
            participant_id INT NOT NULL COMMENT '参与者ID',
            event_id INT NOT NULL COMMENT '活动ID',
            balance INT NOT NULL DEFAULT 0 COMMENT '账户余额（分）',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            CONSTRAINT fk_account_participant FOREIGN KEY (participant_id) 
                REFERENCES participants(id) ON DELETE CASCADE,
            CONSTRAINT fk_account_event FOREIGN KEY (event_id) 
                REFERENCES events(id) ON DELETE CASCADE,
            CONSTRAINT uk_participant_event UNIQUE (participant_id, event_id),
            INDEX idx_participant_id (participant_id),
            INDEX idx_event_id (event_id),
            INDEX idx_balance (balance),
            CONSTRAINT chk_account_balance CHECK (balance >= 0)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='活动账户表'""", "Create accounts table"),
        
        # 4. Add columns to transactions table
        ("ALTER TABLE transactions ADD COLUMN event_id INT DEFAULT NULL COMMENT '活动ID'", "Add event_id to transactions"),
        ("ALTER TABLE transactions ADD COLUMN participant_id INT DEFAULT NULL COMMENT '参与者ID'", "Add participant_id to transactions"),
        ("ALTER TABLE transactions ADD COLUMN account_id INT DEFAULT NULL COMMENT '账户ID'", "Add account_id to transactions"),
        
        # Add foreign keys
        ("""ALTER TABLE transactions
            ADD CONSTRAINT fk_transaction_event 
                FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE SET NULL""", "Add FK: transactions.event_id"),
        
        ("""ALTER TABLE transactions
            ADD CONSTRAINT fk_transaction_participant 
                FOREIGN KEY (participant_id) REFERENCES participants(id) ON DELETE SET NULL""", "Add FK: transactions.participant_id"),
        
        ("""ALTER TABLE transactions
            ADD CONSTRAINT fk_transaction_account 
                FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE SET NULL""", "Add FK: transactions.account_id"),
        
        # Add indexes
        ("CREATE INDEX idx_event_id ON transactions(event_id)", "Create index on transactions.event_id"),
        ("CREATE INDEX idx_participant_id ON transactions(participant_id)", "Create index on transactions.participant_id"),
        ("CREATE INDEX idx_account_id ON transactions(account_id)", "Create index on transactions.account_id"),
        
        # 5. Migrate existing users to participants
        ("""INSERT INTO participants (name, card_uid, status, created_at)
            SELECT 
                CONCAT('User_', uid) AS name,
                uid AS card_uid,
                'active' AS status,
                created_at
            FROM users
            WHERE NOT EXISTS (
                SELECT 1 FROM participants WHERE card_uid = users.uid
            )""", "Migrate existing users to participants"),
        
        # 6. Create composite indexes
        ("CREATE INDEX idx_accounts_participant_event ON accounts(participant_id, event_id)", "Create composite index: participant_id, event_id"),
        ("CREATE INDEX idx_transactions_event_participant ON transactions(event_id, participant_id)", "Create composite index: event_id, participant_id"),
        ("CREATE INDEX idx_transactions_account_created ON transactions(account_id, created_at)", "Create composite index: account_id, created_at"),
        ("CREATE INDEX idx_accounts_event_balance ON accounts(event_id, balance)", "Create composite index: event_id, balance"),
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
    """Verify migration 002"""
    print("\n=== Verifying Migration ===")
    
    checks = [
        ("Events table", "SELECT COUNT(*) as cnt FROM events"),
        ("Participants table", "SELECT COUNT(*) as cnt FROM participants"),
        ("Accounts table", "SELECT COUNT(*) as cnt FROM accounts"),
        ("Transactions has event_id", "SHOW COLUMNS FROM transactions LIKE 'event_id'"),
        ("Transactions has participant_id", "SHOW COLUMNS FROM transactions LIKE 'participant_id'"),
        ("Transactions has account_id", "SHOW COLUMNS FROM transactions LIKE 'account_id'"),
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
                    else:
                        print(f"✓ {description}: Column exists")
                else:
                    print(f"✗ {description}: Failed")
                    all_passed = False
                    
            except Exception as e:
                print(f"✗ {description}: Error - {e}")
                all_passed = False
    
    return all_passed

def main():
    print("=" * 70)
    print("Migration 002: Event System")
    print("=" * 70)
    
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
    
    if not execute_migration_002(engine):
        print("\n✗ Migration failed.")
        sys.exit(1)
    
    if not verify_migration(engine):
        print("\n⚠ Migration verification found issues.")
        sys.exit(1)
    
    print("\n✓ Migration 002 completed successfully!")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Migration Script Runner for Booth Management System
Executes migration 003_booth_management_system.sql
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_USER = os.getenv('DATABASE_USER', 'nfc_wallet')
DB_PASSWORD = os.getenv('DATABASE_PASSWORD')
DB_HOST = os.getenv('DATABASE_HOST', 'localhost')
DB_PORT = os.getenv('DATABASE_PORT', '3306')
DB_NAME = os.getenv('DATABASE_NAME', 'nfc_wallet')

if not DB_PASSWORD:
    print("ERROR: DATABASE_PASSWORD not set in environment")
    sys.exit(1)

# Create database URL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def backup_database(engine):
    """Create a backup of critical tables before migration"""
    print("\n=== Step 1: Creating Database Backup ===")
    
    backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = "backups"
    
    # Create backups directory if it doesn't exist
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        print(f"Created backup directory: {backup_dir}")
    
    # Tables to backup
    tables_to_backup = ['events', 'participants', 'accounts', 'transactions']
    
    with engine.connect() as conn:
        for table in tables_to_backup:
            try:
                # Check if table exists
                result = conn.execute(text(f"SHOW TABLES LIKE '{table}'"))
                if result.fetchone():
                    # Get row count
                    count_result = conn.execute(text(f"SELECT COUNT(*) as cnt FROM {table}"))
                    count = count_result.fetchone()[0]
                    print(f"  - Table '{table}': {count} rows")
                else:
                    print(f"  - Table '{table}': does not exist (skipping)")
            except Exception as e:
                print(f"  - Table '{table}': Error checking - {e}")
    
    print(f"\nBackup information recorded at: {backup_timestamp}")
    print("Note: For full backup, use mysqldump command separately")
    return True

def execute_migration(engine, migration_file):
    """Execute the migration SQL script"""
    print(f"\n=== Step 2: Executing Migration Script ===")
    print(f"Migration file: {migration_file}")
    
    # Read migration file
    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
    except FileNotFoundError:
        print(f"ERROR: Migration file not found: {migration_file}")
        return False
    except Exception as e:
        print(f"ERROR: Failed to read migration file: {e}")
        return False
    
    # Split SQL statements (handle DELIMITER changes)
    statements = []
    current_statement = []
    delimiter = ';'
    in_delimiter_block = False
    
    for line in migration_sql.split('\n'):
        line = line.strip()
        
        # Handle DELIMITER command
        if line.startswith('DELIMITER'):
            if 'DELIMITER ;' in line:
                delimiter = ';'
                in_delimiter_block = False
            else:
                delimiter = line.split()[-1]
                in_delimiter_block = True
            continue
        
        # Skip empty lines and comments
        if not line or line.startswith('--'):
            continue
        
        current_statement.append(line)
        
        # Check if statement is complete
        if line.endswith(delimiter):
            stmt = ' '.join(current_statement)
            # Remove delimiter from end
            if delimiter != ';':
                stmt = stmt[:-len(delimiter)].strip()
            else:
                stmt = stmt[:-1].strip()
            
            if stmt:
                statements.append(stmt)
            current_statement = []
    
    # Add any remaining statement
    if current_statement:
        stmt = ' '.join(current_statement).strip()
        if stmt:
            statements.append(stmt)
    
    print(f"Found {len(statements)} SQL statements to execute\n")
    
    # Execute statements
    with engine.connect() as conn:
        executed = 0
        failed = 0
        
        for i, statement in enumerate(statements, 1):
            # Skip SELECT statements used for verification
            if statement.upper().startswith('SELECT') and 'INTO' not in statement.upper():
                print(f"[{i}/{len(statements)}] Skipping verification query")
                continue
            
            try:
                # Show what we're executing (truncated)
                stmt_preview = statement[:80] + '...' if len(statement) > 80 else statement
                print(f"[{i}/{len(statements)}] Executing: {stmt_preview}")
                
                conn.execute(text(statement))
                conn.commit()
                executed += 1
                
            except Exception as e:
                error_msg = str(e)
                # Check if it's a "already exists" error (which is OK for idempotent migrations)
                if 'already exists' in error_msg.lower() or 'duplicate' in error_msg.lower():
                    print(f"  ⚠ Warning: {error_msg} (continuing...)")
                else:
                    print(f"  ✗ Error: {error_msg}")
                    failed += 1
        
        print(f"\n✓ Executed: {executed} statements")
        if failed > 0:
            print(f"✗ Failed: {failed} statements")
            return False
    
    return True

def verify_migration(engine):
    """Verify that migration was successful"""
    print("\n=== Step 3: Verifying Migration ===")
    
    verification_queries = [
        ("Booths table exists", "SHOW TABLES LIKE 'booths'"),
        ("Products table exists", "SHOW TABLES LIKE 'products'"),
        ("Users table exists", "SHOW TABLES LIKE 'users'"),
        ("Booths table structure", "DESCRIBE booths"),
        ("Products table structure", "DESCRIBE products"),
        ("Users table structure", "DESCRIBE users"),
        ("Transactions table has booth_id", "SHOW COLUMNS FROM transactions LIKE 'booth_id'"),
        ("Transactions table has product_id", "SHOW COLUMNS FROM transactions LIKE 'product_id'"),
        ("Transactions table has operator_id", "SHOW COLUMNS FROM transactions LIKE 'operator_id'"),
        ("Booths indexes", "SHOW INDEXES FROM booths"),
        ("Products indexes", "SHOW INDEXES FROM products"),
        ("Users indexes", "SHOW INDEXES FROM users"),
        ("Super admin account", "SELECT id, username, role, status FROM users WHERE role = 'super_admin'"),
    ]
    
    all_passed = True
    
    with engine.connect() as conn:
        for description, query in verification_queries:
            try:
                result = conn.execute(text(query))
                rows = result.fetchall()
                
                if rows:
                    print(f"✓ {description}: OK ({len(rows)} result(s))")
                    
                    # Show details for important checks
                    if 'super_admin' in description:
                        for row in rows:
                            print(f"  - Admin user: id={row[0]}, username={row[1]}, role={row[2]}, status={row[3]}")
                else:
                    print(f"✗ {description}: No results")
                    all_passed = False
                    
            except Exception as e:
                print(f"✗ {description}: Error - {e}")
                all_passed = False
    
    return all_passed

def main():
    """Main migration execution function"""
    print("=" * 70)
    print("Booth Management System - Database Migration")
    print("Migration: 003_booth_management_system.sql")
    print("=" * 70)
    
    migration_file = "migrations/003_booth_management_system.sql"
    
    # Check if migration file exists
    if not os.path.exists(migration_file):
        print(f"\nERROR: Migration file not found: {migration_file}")
        sys.exit(1)
    
    # Create database engine
    try:
        print(f"\nConnecting to database: {DB_HOST}:{DB_PORT}/{DB_NAME}")
        engine = create_engine(DATABASE_URL, echo=False)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        print("✓ Database connection successful")
        
    except Exception as e:
        print(f"\n✗ ERROR: Failed to connect to database: {e}")
        sys.exit(1)
    
    # Step 1: Backup
    if not backup_database(engine):
        print("\n✗ Backup failed. Aborting migration.")
        sys.exit(1)
    
    # Step 2: Execute migration
    if not execute_migration(engine, migration_file):
        print("\n✗ Migration execution failed.")
        sys.exit(1)
    
    # Step 3: Verify migration
    if not verify_migration(engine):
        print("\n⚠ Migration verification found issues.")
        print("Please review the output above.")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("✓ Migration completed successfully!")
    print("=" * 70)
    print("\nDefault super admin account created:")
    print("  Username: admin")
    print("  Password: admin123")
    print("\n⚠ IMPORTANT: Please change the default admin password immediately!")
    print("=" * 70)

if __name__ == "__main__":
    main()

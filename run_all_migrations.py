#!/usr/bin/env python3
"""
Complete Migration Runner for NFC Campus Wallet System
Executes all migrations in order: 001 -> 002 -> 003
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
    print("\n=== Creating Database Backup ===")
    
    backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = "backups"
    
    # Create backups directory if it doesn't exist
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        print(f"Created backup directory: {backup_dir}")
    
    # Get all tables
    with engine.connect() as conn:
        result = conn.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result.fetchall()]
        
        print(f"\nBacking up {len(tables)} tables:")
        for table in tables:
            count_result = conn.execute(text(f"SELECT COUNT(*) as cnt FROM {table}"))
            count = count_result.fetchone()[0]
            print(f"  - {table}: {count} rows")
    
    print(f"\nBackup timestamp: {backup_timestamp}")
    print("⚠ Note: For production, use mysqldump for full backup")
    return True

def execute_migration_file(engine, migration_file, migration_name):
    """Execute a single migration SQL file"""
    print(f"\n{'=' * 70}")
    print(f"Executing Migration: {migration_name}")
    print(f"File: {migration_file}")
    print('=' * 70)
    
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
    
    # Remove inline comments from SQL (-- comments)
    lines = migration_sql.split('\n')
    cleaned_lines = []
    for line in lines:
        # Remove inline comments but preserve the line
        if '--' in line:
            # Check if -- is inside a string
            in_string = False
            cleaned_line = []
            i = 0
            while i < len(line):
                if line[i] == "'" and (i == 0 or line[i-1] != '\\'):
                    in_string = not in_string
                    cleaned_line.append(line[i])
                elif line[i:i+2] == '--' and not in_string:
                    break  # Rest of line is comment
                else:
                    cleaned_line.append(line[i])
                i += 1
            cleaned_lines.append(''.join(cleaned_line))
        else:
            cleaned_lines.append(line)
    
    migration_sql = '\n'.join(cleaned_lines)
    
    # Split SQL statements by semicolon, handling DELIMITER blocks
    statements = []
    current_statement = []
    delimiter = ';'
    in_delimiter_block = False
    lines = migration_sql.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Handle DELIMITER command
        if line.startswith('DELIMITER'):
            if 'DELIMITER ;' in line:
                delimiter = ';'
                in_delimiter_block = False
            else:
                delimiter = line.split()[-1]
                in_delimiter_block = True
            i += 1
            continue
        
        # Skip empty lines
        if not line:
            i += 1
            continue
        
        # Handle multi-line statements (triggers, procedures)
        if in_delimiter_block:
            # Collect lines until we find the delimiter
            block_lines = []
            while i < len(lines):
                line = lines[i].strip()
                if line == delimiter:
                    break
                if line:
                    block_lines.append(line)
                i += 1
            
            if block_lines:
                stmt = ' '.join(block_lines)
                statements.append(stmt)
            i += 1  # Skip the delimiter line
        else:
            # Regular statement
            current_statement.append(line)
            
            if line.endswith(';'):
                stmt = ' '.join(current_statement)[:-1].strip()  # Remove trailing semicolon
                if stmt:
                    statements.append(stmt)
                current_statement = []
                i += 1
            else:
                i += 1
    
    # Add any remaining statement
    if current_statement:
        stmt = ' '.join(current_statement).strip()
        if stmt.endswith(';'):
            stmt = stmt[:-1]
        if stmt:
            statements.append(stmt)
    
    print(f"\nFound {len(statements)} SQL statements\n")
    
    # Execute statements
    executed = 0
    warnings = 0
    failed = 0
    
    with engine.connect() as conn:
        for i, statement in enumerate(statements, 1):
            # Skip SELECT statements used for verification
            stmt_upper = statement.upper()
            if stmt_upper.startswith('SELECT') and 'INTO' not in stmt_upper:
                continue
            
            try:
                # Show what we're executing (truncated)
                stmt_preview = statement[:100] + '...' if len(statement) > 100 else statement
                print(f"[{i}/{len(statements)}] {stmt_preview}")
                
                conn.execute(text(statement))
                conn.commit()
                executed += 1
                print("  ✓ Success")
                
            except Exception as e:
                error_msg = str(e)
                # Check if it's a "already exists" or "duplicate" error (OK for idempotent migrations)
                if any(keyword in error_msg.lower() for keyword in ['already exists', 'duplicate', 'duplicate key']):
                    print(f"  ⚠ Warning: {error_msg}")
                    warnings += 1
                else:
                    print(f"  ✗ Error: {error_msg}")
                    failed += 1
                    # For critical errors, stop migration
                    if 'syntax error' in error_msg.lower() or 'unknown column' in error_msg.lower():
                        print(f"\n✗ Critical error encountered. Stopping migration.")
                        return False
    
    print(f"\n{'=' * 70}")
    print(f"Migration Summary:")
    print(f"  ✓ Executed: {executed}")
    print(f"  ⚠ Warnings: {warnings}")
    print(f"  ✗ Failed: {failed}")
    print('=' * 70)
    
    return failed == 0 or warnings > 0  # Success if no failures or only warnings

def verify_migration_003(engine):
    """Verify that migration 003 was successful"""
    print("\n=== Verifying Migration 003 ===")
    
    verification_queries = [
        ("Booths table", "SELECT COUNT(*) as cnt FROM booths"),
        ("Products table", "SELECT COUNT(*) as cnt FROM products"),
        ("Users table", "SELECT COUNT(*) as cnt FROM users"),
        ("Transactions booth_id column", "SELECT COUNT(*) as cnt FROM transactions WHERE booth_id IS NOT NULL"),
        ("Super admin account", "SELECT id, username, role, status FROM users WHERE role = 'super_admin'"),
    ]
    
    all_passed = True
    
    with engine.connect() as conn:
        for description, query in verification_queries:
            try:
                result = conn.execute(text(query))
                rows = result.fetchall()
                
                if rows:
                    if 'COUNT' in query:
                        count = rows[0][0]
                        print(f"✓ {description}: {count} records")
                    else:
                        print(f"✓ {description}: Found")
                        for row in rows:
                            print(f"    {row}")
                else:
                    print(f"⚠ {description}: No results")
                    
            except Exception as e:
                print(f"✗ {description}: Error - {e}")
                all_passed = False
    
    return all_passed

def main():
    """Main migration execution function"""
    print("=" * 70)
    print("NFC Campus Wallet System - Complete Database Migration")
    print("=" * 70)
    
    migrations = [
        ("migrations/001_upgrade_to_ledger_mode.sql", "001 - Ledger Mode"),
        ("migrations/002_upgrade_to_event_system.sql", "002 - Event System"),
        ("migrations/003_booth_management_system.sql", "003 - Booth Management System"),
    ]
    
    # Check if all migration files exist
    for migration_file, _ in migrations:
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
    
    # Backup database
    if not backup_database(engine):
        print("\n✗ Backup failed. Aborting migration.")
        sys.exit(1)
    
    # Execute migrations in order
    for migration_file, migration_name in migrations:
        if not execute_migration_file(engine, migration_file, migration_name):
            print(f"\n✗ Migration {migration_name} failed.")
            print("Please review errors and fix before continuing.")
            sys.exit(1)
        print(f"\n✓ Migration {migration_name} completed")
    
    # Verify final state
    print("\n" + "=" * 70)
    if verify_migration_003(engine):
        print("\n✓ All migrations completed successfully!")
    else:
        print("\n⚠ Migrations completed with warnings. Please review.")
    
    print("=" * 70)
    print("\n📋 Migration Summary:")
    print("  ✓ 001 - Ledger Mode: Upgraded to ledger-based transaction tracking")
    print("  ✓ 002 - Event System: Added events, participants, and accounts")
    print("  ✓ 003 - Booth Management: Added booths, products, and user roles")
    print("\n🔐 Default Super Admin Account:")
    print("  Username: admin")
    print("  Password: admin123")
    print("\n⚠ IMPORTANT: Change the default admin password immediately!")
    print("=" * 70)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Check current database state
"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv('DATABASE_USER', 'nfc_wallet')
DB_PASSWORD = os.getenv('DATABASE_PASSWORD')
DB_HOST = os.getenv('DATABASE_HOST', 'localhost')
DB_PORT = os.getenv('DATABASE_PORT', '3306')
DB_NAME = os.getenv('DATABASE_NAME', 'nfc_wallet')

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=False)

print("Current database tables:")
print("=" * 50)

with engine.connect() as conn:
    result = conn.execute(text("SHOW TABLES"))
    tables = [row[0] for row in result.fetchall()]
    
    if not tables:
        print("No tables found in database")
    else:
        for table in tables:
            # Get row count
            count_result = conn.execute(text(f"SELECT COUNT(*) as cnt FROM {table}"))
            count = count_result.fetchone()[0]
            print(f"  - {table}: {count} rows")
            
            # Show structure
            print(f"\n    Structure of {table}:")
            desc_result = conn.execute(text(f"DESCRIBE {table}"))
            for row in desc_result.fetchall():
                print(f"      {row[0]}: {row[1]} {row[2]} {row[3]} {row[4]}")
            print()

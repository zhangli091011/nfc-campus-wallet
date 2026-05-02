#!/usr/bin/env python3
"""Fix migration 002 - migrate users to participants"""

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

with engine.connect() as conn:
    # Migrate users to participants with collation fix
    result = conn.execute(text("""
        INSERT INTO participants (name, card_uid, status, created_at)
        SELECT 
            CONCAT('User_', uid) AS name,
            CAST(uid AS CHAR CHARACTER SET utf8mb4) COLLATE utf8mb4_unicode_ci AS card_uid,
            'active' AS status,
            created_at
        FROM users
        WHERE NOT EXISTS (
            SELECT 1 FROM participants 
            WHERE card_uid = CAST(users.uid AS CHAR CHARACTER SET utf8mb4) COLLATE utf8mb4_unicode_ci
        )
    """))
    conn.commit()
    print(f"✓ Migrated {result.rowcount} users to participants")

print("✓ Migration 002 fix completed")

"""
Apply school_inspector role migration.

This script updates the users table CHECK constraint to allow the
'school_inspector' role (校方巡查，只读权限).

Usage:
    python apply_school_inspector_migration.py
"""

import sys
import logging
from pathlib import Path

# Ensure project root is on sys.path so we can import core.*
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import create_engine, text

from core.config import get_settings, load_settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def apply_migration() -> None:
    load_settings()
    settings = get_settings()
    engine = create_engine(settings.database_url)

    migration_path = Path(__file__).resolve().parent / "migrations" / "013_add_school_inspector_role.sql"
    if not migration_path.exists():
        raise FileNotFoundError(f"Migration file not found: {migration_path}")

    logger.info("Applying migration 013_add_school_inspector_role.sql ...")

    with engine.begin() as conn:
        # 先清理旧约束（不同版本 MySQL 的语法差异容忍）
        try:
            conn.execute(text("ALTER TABLE users DROP CHECK chk_user_role"))
            logger.info("Dropped old CHECK constraint via DROP CHECK")
        except Exception as e:
            logger.info(f"DROP CHECK skipped: {e}")
            try:
                conn.execute(text("ALTER TABLE users DROP CONSTRAINT chk_user_role"))
                logger.info("Dropped old CHECK constraint via DROP CONSTRAINT")
            except Exception as e2:
                logger.info(f"DROP CONSTRAINT skipped: {e2}")

        # 添加新约束，包含 school_inspector
        conn.execute(
            text(
                "ALTER TABLE users ADD CONSTRAINT chk_user_role "
                "CHECK (role IN ('super_admin', 'event_admin', 'booth_cashier', "
                "'issuer', 'reviewer', 'bank_clerk', 'merchant', 'school_inspector'))"
            )
        )
        logger.info("Added new CHECK constraint with school_inspector role")

    logger.info("✓ Migration applied successfully")


if __name__ == "__main__":
    try:
        apply_migration()
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)

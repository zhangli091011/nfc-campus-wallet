#!/usr/bin/env python3
"""
执行 bank_clerk 角色迁移并更新用户数据。

步骤：
1. 修改 users.role 的 CHECK 约束以容纳 bank_clerk
2. 将现有 bank_clerk 用户的 role 更新为 bank_clerk
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import load_settings
from core.database import init_database
import core.database as db_module
from sqlalchemy import text


def main():
    print("=" * 60)
    print("应用 bank_clerk 角色迁移")
    print("=" * 60)

    load_settings()
    init_database()
    engine = db_module.engine

    with engine.begin() as conn:
        # 1. 修改 CHECK 约束
        print("\n1. 修改 users.role CHECK 约束...")
        try:
            conn.execute(text("ALTER TABLE users DROP CHECK chk_user_role"))
            print("   旧约束已删除")
        except Exception as e:
            # 约束不存在时跳过
            print(f"   (旧约束可能不存在: {e})")

        conn.execute(text(
            "ALTER TABLE users ADD CONSTRAINT chk_user_role "
            "CHECK (role IN ('super_admin', 'event_admin', 'booth_cashier', "
            "'issuer', 'reviewer', 'bank_clerk'))"
        ))
        print("   新约束已添加 (包含 bank_clerk)")

        # 2. 升级现有 bank_clerk 用户
        print("\n2. 检查 bank_clerk 账号...")
        row = conn.execute(
            text("SELECT id, username, role FROM users WHERE username = 'bank_clerk'")
        ).fetchone()

        if row:
            print(f"   找到账号: id={row.id}, username={row.username}, role={row.role}")
            if row.role != 'bank_clerk':
                conn.execute(text(
                    "UPDATE users SET role = 'bank_clerk' WHERE username = 'bank_clerk'"
                ))
                print(f"   ✅ 已将 role 从 '{row.role}' 更新为 'bank_clerk'")
            else:
                print("   ✅ role 已经是 bank_clerk")
        else:
            print("   未找到 bank_clerk 账号（请运行 add_investment_system.py 创建）")

    print("\n" + "=" * 60)
    print("✅ 迁移完成")
    print("=" * 60)


if __name__ == "__main__":
    main()

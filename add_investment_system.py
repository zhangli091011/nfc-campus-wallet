#!/usr/bin/env python3
"""
添加投资办理系统所需的数据

包括：
- 投资办理摊位（中央银行）
- 专用账号 bank_clerk（密码 invest123）
"""

import sys
import os
from datetime import datetime, date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import load_settings
from core.database import init_database
import core.database as db_module
from core.security import hash_password
from models.event import Event
from models.booth import Booth
from models.user import User


def main():
    print("=" * 60)
    print("添加投资办理系统数据")
    print("=" * 60)

    load_settings()
    init_database()
    db = db_module.SessionLocal()

    try:
        # --------------------------------------------------------
        # 1. 确保有一个 active 活动
        # --------------------------------------------------------
        print("\n1. 检查活动...")
        event = db.query(Event).filter(
            Event.status == 'active'
        ).first()

        if not event:
            today = date.today()
            event = Event(
                name="投资办理活动",
                start_date=datetime.combine(today - timedelta(days=1), datetime.min.time()),
                end_date=datetime.combine(today + timedelta(days=60), datetime.min.time()),
                status='active',
                allow_recharge=True,
                allow_payment=True
            )
            db.add(event)
            db.commit()
            db.refresh(event)
            print(f"   已创建活动: ID={event.id}, Name={event.name}")
        else:
            print(f"   使用现有活动: ID={event.id}, Name={event.name}")

        # --------------------------------------------------------
        # 2. 创建投资办理摊位（中央银行）
        # --------------------------------------------------------
        print("\n2. 检查投资办理摊位...")
        bank_booth_name = "官方中央银行"
        bank_booth = db.query(Booth).filter(
            Booth.name == bank_booth_name
        ).first()

        if not bank_booth:
            bank_booth = Booth(
                event_id=event.id,
                name=bank_booth_name,
                class_name="投资办理中心",
                status='active'
            )
            db.add(bank_booth)
            db.commit()
            db.refresh(bank_booth)
            print(f"   已创建投资办理摊位: ID={bank_booth.id}, Name={bank_booth.name}")
        else:
            if bank_booth.status != 'active':
                bank_booth.status = 'active'
                db.commit()
            print(f"   投资办理摊位已存在: ID={bank_booth.id}, Name={bank_booth.name}")

        # --------------------------------------------------------
        # 3. 创建专用账号 bank_clerk
        # --------------------------------------------------------
        print("\n3. 检查投资办理员账号...")
        bank_clerk_username = "bank_clerk"
        bank_clerk = db.query(User).filter(
            User.username == bank_clerk_username
        ).first()

        if not bank_clerk:
            bank_clerk = User(
                username=bank_clerk_username,
                password_hash=hash_password("invest123"),
                role='bank_clerk',  # 专用角色：投资办理员
                status='active'
            )
            db.add(bank_clerk)
            db.commit()
            db.refresh(bank_clerk)
            print(f"   已创建投资办理员账号: {bank_clerk.username} / invest123 (role=bank_clerk)")
        else:
            # 若已存在旧账号（role=super_admin），升级为专用角色 bank_clerk
            if bank_clerk.role != 'bank_clerk':
                print(f"   检测到旧账号 (role={bank_clerk.role})，升级为 bank_clerk")
                bank_clerk.role = 'bank_clerk'
                db.commit()
            if bank_clerk.status != 'active':
                bank_clerk.status = 'active'
                db.commit()
            print(f"   投资办理员账号已存在: {bank_clerk.username} (role=bank_clerk)")
            print(f"   如需重置密码，可手动执行 UPDATE 语句")

        # --------------------------------------------------------
        # 总结
        # --------------------------------------------------------
        print("\n" + "=" * 60)
        print("✅ 投资办理系统数据添加完成！")
        print("=" * 60)
        print(f"\n📋 关键信息:")
        print(f"   活动ID:       {event.id}")
        print(f"   活动名称:     {event.name}")
        print(f"   投资摊位ID:   {bank_booth.id}  (安卓端识别用)")
        print(f"   投资摊位名称: {bank_booth.name}")
        print(f"\n📱 投资办理员账号:")
        print(f"   用户名: bank_clerk")
        print(f"   密码:   invest123")
        print(f"   角色:   bank_clerk (投资办理员专用角色)")
        print(f"\n💡 Android 端登录流程:")
        print(f"   1. 使用 bank_clerk / invest123 登录")
        print(f"   2. 根据 role=bank_clerk 自动进入【官方中央银行 - 投资办理终端】界面")
        print(f"   3. 学生刷卡，选择投资摊位，输入股数，确认投资")

    except Exception as e:
        db.rollback()
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

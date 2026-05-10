#!/usr/bin/env python3
"""
添加测试店铺数据

为安卓端admin登录后自动进入测试店铺提供数据支持。
- 创建测试活动（如果不存在）
- 创建测试摊位（active 状态）
- 添加一些测试商品
"""

import sys
import os
from datetime import datetime, date, timedelta, timezone

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import load_settings
from core.database import init_database
import core.database as db_module
from models.event import Event
from models.booth import Booth
from models.product import Product


def main():
    print("=" * 60)
    print("添加测试店铺数据")
    print("=" * 60)
    
    # 加载配置和初始化数据库
    print("\n1. 加载配置...")
    load_settings()
    init_database()
    print("   配置加载完成")
    
    db = db_module.SessionLocal()
    
    try:
        # ========================================================
        # 步骤1: 检查/创建测试活动
        # ========================================================
        print("\n2. 检查测试活动...")
        
        test_event_name = "测试活动"
        event = db.query(Event).filter(Event.name == test_event_name).first()
        
        if event:
            print(f"   测试活动已存在: ID={event.id}, Name={event.name}, Status={event.status}")
            
            # 如果活动状态不是 active，更新为 active
            if event.status != 'active':
                event.status = 'active'
                db.commit()
                print(f"   活动状态已更新为 active")
            
            # 检查活动时间范围，确保当前时间在范围内
            today = date.today()
            start = event.start_date.date() if isinstance(event.start_date, datetime) else event.start_date
            end = event.end_date.date() if isinstance(event.end_date, datetime) else event.end_date
            
            if not (start <= today <= end):
                # 扩展时间范围
                event.start_date = datetime.combine(today - timedelta(days=1), datetime.min.time())
                event.end_date = datetime.combine(today + timedelta(days=30), datetime.min.time())
                db.commit()
                print(f"   活动时间已更新: {event.start_date.date()} ~ {event.end_date.date()}")
        else:
            today = date.today()
            event = Event(
                name=test_event_name,
                start_date=datetime.combine(today - timedelta(days=1), datetime.min.time()),
                end_date=datetime.combine(today + timedelta(days=30), datetime.min.time()),
                status='active',
                allow_recharge=True,
                allow_payment=True
            )
            db.add(event)
            db.commit()
            db.refresh(event)
            print(f"   已创建测试活动: ID={event.id}, Name={event.name}")
        
        # ========================================================
        # 步骤2: 检查/创建测试摊位
        # ========================================================
        print("\n3. 检查测试摊位...")
        
        test_booth_name = "测试店铺"
        booth = db.query(Booth).filter(
            Booth.name == test_booth_name,
            Booth.event_id == event.id
        ).first()
        
        if booth:
            print(f"   测试摊位已存在: ID={booth.id}, Name={booth.name}, Status={booth.status}")
            
            # 确保状态是 active
            if booth.status != 'active':
                booth.status = 'active'
                db.commit()
                print(f"   摊位状态已更新为 active")
        else:
            booth = Booth(
                event_id=event.id,
                name=test_booth_name,
                class_name="测试班级",
                status='active'
            )
            db.add(booth)
            db.commit()
            db.refresh(booth)
            print(f"   已创建测试摊位: ID={booth.id}, Name={booth.name}")
        
        # ========================================================
        # 步骤3: 添加测试商品
        # ========================================================
        print("\n4. 检查测试商品...")
        
        test_products = [
            {"name": "可乐", "price": 500, "cost_price": 200, "stock": 100},  # 5元
            {"name": "雪碧", "price": 500, "cost_price": 200, "stock": 100},  # 5元
            {"name": "矿泉水", "price": 200, "cost_price": 80, "stock": 200},  # 2元
            {"name": "薯片", "price": 800, "cost_price": 400, "stock": 50},   # 8元
            {"name": "巧克力", "price": 1000, "cost_price": 500, "stock": 50}, # 10元
            {"name": "鸡米花", "price": 1500, "cost_price": 800, "stock": 30}, # 15元
            {"name": "关东煮", "price": 2000, "cost_price": 1000, "stock": 30}, # 20元
            {"name": "奶茶", "price": 1200, "cost_price": 500, "stock": 50},  # 12元
        ]
        
        existing_count = 0
        created_count = 0
        
        for product_data in test_products:
            existing = db.query(Product).filter(
                Product.booth_id == booth.id,
                Product.name == product_data["name"]
            ).first()
            
            if existing:
                existing_count += 1
                # 确保商品启用并更新库存
                if not existing.enabled:
                    existing.enabled = True
                if existing.stock is not None and existing.stock < 10:
                    existing.stock = product_data["stock"]
                db.commit()
            else:
                product = Product(
                    booth_id=booth.id,
                    name=product_data["name"],
                    price=product_data["price"],
                    cost_price=product_data["cost_price"],
                    stock=product_data["stock"],
                    enabled=True
                )
                db.add(product)
                created_count += 1
        
        db.commit()
        print(f"   已存在商品: {existing_count} 个")
        print(f"   新建商品: {created_count} 个")
        
        # ========================================================
        # 步骤4: 检查其他 active 状态的摊位
        # ========================================================
        print("\n5. 检查所有 active 状态的摊位...")
        
        active_booths = db.query(Booth).filter(Booth.status == 'active').all()
        print(f"   当前共有 {len(active_booths)} 个 active 摊位:")
        
        for b in active_booths:
            event_info = db.query(Event).filter(Event.id == b.event_id).first()
            event_active = event_info.is_active() if event_info else False
            marker = "⭐" if b.id == booth.id else "  "
            print(f"   {marker} ID={b.id}, Name='{b.name}', Event='{event_info.name if event_info else 'N/A'}', EventActive={event_active}")
        
        # ========================================================
        # 如果存在其他 active 摊位，提示用户
        # ========================================================
        if len(active_booths) > 1:
            print("\n" + "=" * 60)
            print("⚠️  注意：当前存在多个 active 摊位！")
            print("=" * 60)
            print("\n由于安卓端的逻辑：")
            print("  - 如果 active 摊位只有 1 个，会自动进入该摊位")
            print("  - 如果 active 摊位有多个，会显示选择列表")
            print("\n如果希望 admin 登录后自动进入【测试店铺】，请选择操作：")
            print("  选项1: 将其他摊位设为 inactive（推荐）")
            print("  选项2: 保持多摊位，让 admin 手动选择")
            
            response = input("\n是否要将其他摊位设为 inactive？(y/N): ").strip().lower()
            
            if response == 'y':
                disabled_count = 0
                for b in active_booths:
                    if b.id != booth.id:
                        b.status = 'inactive'
                        disabled_count += 1
                db.commit()
                print(f"\n✅ 已将 {disabled_count} 个其他摊位设为 inactive")
                print(f"✅ 现在只有【测试店铺】是 active 状态")
            else:
                print("\n保持多摊位状态，admin 登录后需要手动选择")
        
        # ========================================================
        # 总结
        # ========================================================
        print("\n" + "=" * 60)
        print("✅ 测试数据添加完成！")
        print("=" * 60)
        print(f"\n📋 测试数据:")
        print(f"   - 活动ID: {event.id}")
        print(f"   - 活动名称: {event.name}")
        print(f"   - 摊位ID: {booth.id}")
        print(f"   - 摊位名称: {booth.name}")
        print(f"   - 商品数量: {db.query(Product).filter(Product.booth_id == booth.id).count()} 个")
        
        print(f"\n📱 安卓端使用说明:")
        print(f"   1. 使用 admin / admin123 登录")
        print(f"   2. 如果只有一个 active 摊位，会自动进入【测试店铺】")
        print(f"   3. 如果有多个 active 摊位，需要手动选择")
        
        print(f"\n🔧 API 验证:")
        print(f"   GET /booths?status=active")
        print(f"   应该返回包含【测试店铺】的列表")
    
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

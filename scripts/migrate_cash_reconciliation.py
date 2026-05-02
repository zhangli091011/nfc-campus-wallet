"""
Database Migration Script for Cash Reconciliation Table.

添加现金对账表的数据库迁移脚本。
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text, create_engine
from core.database import init_database
from core.config import load_settings, get_settings


def migrate():
    """执行数据库迁移"""
    print("=" * 60)
    print("Database Migration - Cash Reconciliation Table")
    print("=" * 60)
    
    # 加载配置
    print("\n⚙️  加载配置...")
    try:
        load_settings()
        settings = get_settings()
        print("✅ 配置加载完成")
        print(f"   数据库: {settings.database_host}:{settings.database_port}/{settings.database_name}")
    except Exception as e:
        print(f"❌ 配置加载失败: {str(e)}")
        print("\n请确保 .env 文件存在并配置正确")
        sys.exit(1)
    
    # 创建数据库引擎
    print("\n🔌 连接数据库...")
    try:
        database_url = (
            f"mysql+pymysql://{settings.database_user}:{settings.database_password}"
            f"@{settings.database_host}:{settings.database_port}/{settings.database_name}"
        )
        engine = create_engine(database_url)
        
        # 测试连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        print("✅ 数据库连接成功")
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        print("\n请检查:")
        print("  1. MySQL 服务是否运行")
        print("  2. 数据库连接信息是否正确")
        print("  3. 数据库用户是否有权限")
        sys.exit(1)
    
    # 创建所有表（包括新增的 cash_reconciliation 表）
    print("\n📦 创建数据库表...")
    try:
        # 导入所有模型以确保它们被注册到 Base.metadata
        from models import (
            User, Transaction, Merchant, Event, Participant,
            Account, Booth, Product, CashReconciliation
        )
        from core.database import Base
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表创建完成")
    except Exception as e:
        print(f"❌ 数据库表创建失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # 验证表是否存在
    print("\n🔍 验证表结构...")
    
    with engine.connect() as conn:
        result = conn.execute(text(
            "SHOW TABLES LIKE 'booth_cash_reconciliations'"
        ))
        
        if result.fetchone():
            print("✅ booth_cash_reconciliations 表已创建")
            
            # 显示表结构
            result = conn.execute(text(
                "DESCRIBE booth_cash_reconciliations"
            ))
            
            print("\n📋 表结构:")
            for row in result:
                print(f"  - {row[0]}: {row[1]}")
        else:
            print("❌ booth_cash_reconciliations 表不存在")
            sys.exit(1)
    
    print("\n✅ 迁移完成！")


if __name__ == "__main__":
    migrate()

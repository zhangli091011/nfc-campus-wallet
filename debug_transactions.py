"""
调试交易接口500错误的脚本
"""
import sys
import logging
from sqlalchemy.orm import Session

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 导入必要的模块
from core.database import get_db, init_database
from core.config import load_settings
from services.transaction_service import TransactionService

def debug_transactions():
    """调试交易查询"""
    try:
        # 初始化
        load_settings()
        init_database()
        
        # 获取数据库会话
        db = next(get_db())
        
        # 创建服务
        service = TransactionService(db)
        
        # 测试查询
        print("=" * 60)
        print("测试交易查询 (event_id=2)")
        print("=" * 60)
        
        try:
            result = service.get_event_transaction_history(
                event_id=2,
                limit=20,
                offset=0
            )
            
            print(f"\n✅ 查询成功!")
            print(f"总记录数: {result['total_count']}")
            print(f"返回记录数: {len(result['transactions'])}")
            
            if result['transactions']:
                print("\n第一条记录:")
                first_txn = result['transactions'][0]
                for key, value in first_txn.items():
                    print(f"  {key}: {value}")
            else:
                print("\n⚠️  没有找到交易记录")
                
        except Exception as e:
            print(f"\n❌ 查询失败!")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            import traceback
            print("\n完整堆栈:")
            traceback.print_exc()
            
    except Exception as e:
        print(f"\n❌ 初始化失败!")
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    debug_transactions()

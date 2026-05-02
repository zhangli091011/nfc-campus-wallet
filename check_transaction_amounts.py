"""
检查和显示交易记录的金额
"""
import sys
sys.path.insert(0, '.')

from app.config import load_settings
from app.database import init_database, get_db
from models.transaction import Transaction

# 加载配置
load_settings()

# 初始化数据库
init_database()

# 获取数据库会话
db = next(get_db())

try:
    # 查询最近的交易记录
    transactions = db.query(Transaction).order_by(Transaction.id.desc()).limit(10).all()
    
    print("最近10条交易记录：")
    print("-" * 80)
    print(f"{'ID':<5} {'类型':<10} {'金额(分)':<12} {'金额(元)':<12} {'创建时间':<20}")
    print("-" * 80)
    
    for txn in transactions:
        print(f"{txn.id:<5} {txn.type:<10} {txn.amount:<12} {txn.amount/100.0:<12.2f} {txn.created_at}")
    
    print("\n" + "=" * 80)
    print("说明：")
    print("- 金额(分)：数据库存储的原始值，应该是元金额×100")
    print("- 金额(元)：显示给用户的值，应该是金额(分)÷100")
    print("- 如果111元商品显示为¥1.11，说明数据库中存储的是111而不是11100")
    print("=" * 80)
    
finally:
    db.close()

"""
修复历史交易记录中错误的金额

问题：旧版本安卓端创建的交易记录，金额单位错误（存储为元而不是分）
解决：将这些交易的金额乘以100，同时更新余额字段
"""
import sys
sys.path.insert(0, '.')

from app.config import load_settings
from app.database import init_database, get_db
from models.transaction import Transaction
from sqlalchemy import and_

# 加载配置
load_settings()

# 初始化数据库
init_database()

# 获取数据库会话
db = next(get_db())

try:
    print("=" * 80)
    print("修复历史交易记录金额")
    print("=" * 80)
    
    # 查询所有可疑的交易（金额小于1000分 = 10元，很可能是错误的）
    # 排除充值记录，因为充值金额可能本来就小
    suspicious_txns = db.query(Transaction).filter(
        and_(
            Transaction.amount < 1000,  # 小于10元
            Transaction.type == 'pay'    # 只检查支付记录
        )
    ).all()
    
    if not suspicious_txns:
        print("✓ 没有发现需要修复的交易记录")
        print("=" * 80)
        sys.exit(0)
    
    print(f"\n发现 {len(suspicious_txns)} 条可疑交易记录：")
    print("-" * 80)
    print(f"{'ID':<5} {'类型':<10} {'当前金额(分)':<15} {'应为金额(分)':<15} {'卡号':<12}")
    print("-" * 80)
    
    for txn in suspicious_txns:
        print(f"{txn.id:<5} {txn.type:<10} {txn.amount:<15} {txn.amount * 100:<15} {txn.card_uid:<12}")
    
    print("-" * 80)
    print("\n⚠️  警告：此操作将修改数据库中的交易记录！")
    print("修复内容：")
    print("1. 将 amount 字段乘以 100")
    print("2. 将 balance_before 字段乘以 100")
    print("3. 将 balance_after 字段乘以 100")
    print("\n建议：在执行前先备份数据库！")
    
    response = input("\n是否继续修复？(yes/no): ")
    
    if response.lower() != 'yes':
        print("操作已取消")
        sys.exit(0)
    
    print("\n开始修复...")
    fixed_count = 0
    
    for txn in suspicious_txns:
        old_amount = txn.amount
        old_balance_before = txn.balance_before
        old_balance_after = txn.balance_after
        
        # 修复金额（乘以100）
        txn.amount = txn.amount * 100
        txn.balance_before = txn.balance_before * 100
        txn.balance_after = txn.balance_after * 100
        
        print(f"  修复交易 {txn.id}: {old_amount} -> {txn.amount} 分")
        fixed_count += 1
    
    # 提交更改
    db.commit()
    
    print(f"\n✓ 成功修复 {fixed_count} 条交易记录")
    print("=" * 80)
    
    # 显示修复后的结果
    print("\n修复后的交易记录：")
    print("-" * 80)
    print(f"{'ID':<5} {'类型':<10} {'金额(分)':<12} {'金额(元)':<12} {'创建时间':<20}")
    print("-" * 80)
    
    for txn in suspicious_txns:
        db.refresh(txn)  # 刷新以获取最新数据
        print(f"{txn.id:<5} {txn.type:<10} {txn.amount:<12} {txn.amount/100.0:<12.2f} {txn.created_at}")
    
    print("-" * 80)
    print("\n⚠️  重要提示：")
    print("1. 这些交易对应的账户余额可能也需要修正")
    print("2. 建议检查相关参与者的账户余额是否正确")
    print("3. 如果余额不正确，可能需要手动调整或重新计算")
    print("=" * 80)
    
except Exception as e:
    db.rollback()
    print(f"\n✗ 修复失败: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    db.close()

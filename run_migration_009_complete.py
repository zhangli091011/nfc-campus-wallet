"""
执行完整的数据库迁移: 添加所有缺失的列到 transactions 表
"""
import pymysql
from core.config import load_settings, get_settings

def run_migration():
    """执行迁移"""
    try:
        # 加载配置
        load_settings()
        settings = get_settings()
        
        # 连接数据库
        connection = pymysql.connect(
            host=settings.database_host,
            port=settings.database_port,
            user=settings.database_user,
            password=settings.database_password,
            database=settings.database_name,
            charset='utf8mb4'
        )
        
        print("=" * 60)
        print("执行完整迁移: 添加所有缺失的列")
        print("=" * 60)
        
        # 需要添加的列定义
        columns_to_add = [
            ('card_uid', 'VARCHAR(32) NULL AFTER uid', 'idx_transactions_card_uid'),
            ('merchant_id', 'VARCHAR(64) NULL AFTER balance_after', 'idx_transactions_merchant_id'),
            ('related_txn_id', 'INT NULL AFTER merchant_id', 'idx_transactions_related_txn_id'),
            ('booth_operator_id', 'INT NULL AFTER product_id', 'idx_transactions_booth_operator_id'),
        ]
        
        with connection.cursor() as cursor:
            for col_name, col_def, index_name in columns_to_add:
                # 检查列是否存在
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.COLUMNS 
                    WHERE TABLE_SCHEMA = %s 
                      AND TABLE_NAME = 'transactions' 
                      AND COLUMN_NAME = %s
                """, (settings.database_name, col_name))
                
                col_exists = cursor.fetchone()[0]
                
                if col_exists:
                    print(f"✅ {col_name} 列已存在")
                else:
                    print(f"📝 添加 {col_name} 列...")
                    cursor.execute(f"ALTER TABLE transactions ADD COLUMN {col_name} {col_def}")
                    if index_name:
                        cursor.execute(f"ALTER TABLE transactions ADD INDEX {index_name} ({col_name})")
                    connection.commit()
                    print(f"✅ {col_name} 列添加成功")
            
            # 添加外键约束（如果不存在）
            print("\n📝 检查外键约束...")
            
            # related_txn_id 外键
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.TABLE_CONSTRAINTS 
                WHERE TABLE_SCHEMA = %s 
                  AND TABLE_NAME = 'transactions' 
                  AND CONSTRAINT_NAME = 'fk_transactions_related_txn'
            """, (settings.database_name,))
            
            if cursor.fetchone()[0] == 0:
                try:
                    cursor.execute("""
                        ALTER TABLE transactions 
                        ADD CONSTRAINT fk_transactions_related_txn 
                        FOREIGN KEY (related_txn_id) REFERENCES transactions(id) 
                        ON DELETE SET NULL
                    """)
                    connection.commit()
                    print("✅ related_txn_id 外键添加成功")
                except Exception as e:
                    print(f"⚠️  related_txn_id 外键添加失败 (可能已存在): {e}")
            else:
                print("✅ related_txn_id 外键已存在")
            
            # booth_operator_id 外键
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.TABLE_CONSTRAINTS 
                WHERE TABLE_SCHEMA = %s 
                  AND TABLE_NAME = 'transactions' 
                  AND CONSTRAINT_NAME = 'fk_transactions_booth_operator'
            """, (settings.database_name,))
            
            if cursor.fetchone()[0] == 0:
                try:
                    cursor.execute("""
                        ALTER TABLE transactions 
                        ADD CONSTRAINT fk_transactions_booth_operator 
                        FOREIGN KEY (booth_operator_id) REFERENCES users(id) 
                        ON DELETE SET NULL
                    """)
                    connection.commit()
                    print("✅ booth_operator_id 外键添加成功")
                except Exception as e:
                    print(f"⚠️  booth_operator_id 外键添加失败 (可能已存在): {e}")
            else:
                print("✅ booth_operator_id 外键已存在")
            
            # 验证表结构
            print("\n当前 transactions 表结构:")
            cursor.execute("DESCRIBE transactions")
            for row in cursor.fetchall():
                print(f"  {row[0]}: {row[1]} {row[2]} {row[3]} {row[4]}")
        
        connection.close()
        print("\n" + "=" * 60)
        print("✅ 完整迁移完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = run_migration()
    exit(0 if success else 1)

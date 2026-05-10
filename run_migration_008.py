"""
执行数据库迁移 008: 添加 uid 列到 transactions 表
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
        print("执行迁移 008: 添加 uid 列")
        print("=" * 60)
        
        with connection.cursor() as cursor:
            # 检查列是否存在
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                  AND TABLE_NAME = 'transactions' 
                  AND COLUMN_NAME = 'uid'
            """, (settings.database_name,))
            
            col_exists = cursor.fetchone()[0]
            
            if col_exists:
                print("✅ uid 列已存在，无需添加")
            else:
                print("📝 添加 uid 列...")
                cursor.execute("""
                    ALTER TABLE transactions 
                    ADD COLUMN uid VARCHAR(32) NULL AFTER id,
                    ADD INDEX idx_transactions_uid (uid)
                """)
                connection.commit()
                print("✅ uid 列添加成功")
            
            # 验证表结构
            print("\n当前 transactions 表结构:")
            cursor.execute("DESCRIBE transactions")
            for row in cursor.fetchall():
                print(f"  {row[0]}: {row[1]} {row[2]} {row[3]} {row[4]}")
        
        connection.close()
        print("\n" + "=" * 60)
        print("✅ 迁移 008 完成")
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

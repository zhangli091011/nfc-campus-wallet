"""
运行股票市场系统数据库迁移脚本
"""

import mysql.connector
from core.config import get_settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """运行股票市场系统迁移"""
    settings = get_settings()
    
    # 解析数据库URL
    # mysql+pymysql://user:password@host:port/database
    db_url = settings.database_url
    parts = db_url.replace('mysql+pymysql://', '').split('@')
    user_pass = parts[0].split(':')
    host_db = parts[1].split('/')
    host_port = host_db[0].split(':')
    
    user = user_pass[0]
    password = user_pass[1]
    host = host_port[0]
    port = int(host_port[1]) if len(host_port) > 1 else 3306
    database = host_db[1]
    
    logger.info(f"连接数据库: {host}:{port}/{database}")
    
    # 连接数据库
    conn = mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database
    )
    
    cursor = conn.cursor()
    
    try:
        # 读取迁移脚本
        with open('migrations/006_stock_market_system.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # 分割并执行SQL语句
        statements = []
        current_statement = []
        
        for line in sql_script.split('\n'):
            # 跳过注释和空行
            line = line.strip()
            if not line or line.startswith('--'):
                continue
            
            current_statement.append(line)
            
            # 如果行以分号结尾，表示一条语句结束
            if line.endswith(';'):
                statement = ' '.join(current_statement)
                statements.append(statement)
                current_statement = []
        
        # 执行所有语句
        for statement in statements:
            if statement.strip():
                try:
                    logger.info(f"执行: {statement[:100]}...")
                    cursor.execute(statement)
                    conn.commit()
                    logger.info("✅ 成功")
                except mysql.connector.Error as e:
                    if 'already exists' in str(e).lower():
                        logger.warning(f"⚠️  表已存在，跳过")
                    else:
                        logger.error(f"❌ 失败: {e}")
                        raise
        
        logger.info("🎉 股票市场系统迁移完成！")
        
    except Exception as e:
        logger.error(f"迁移失败: {e}")
        conn.rollback()
        raise
    
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    from core.config import load_settings
    load_settings()
    run_migration()

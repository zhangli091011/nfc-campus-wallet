#!/bin/bash

# ============================================================================
# Database Reset Script
# 数据库重置脚本
# ============================================================================
# 
# 功能：
# 1. 清空所有表、视图、存储过程
# 2. 重新初始化数据库
# 
# 使用方法：
# bash reset_database.sh
# 
# ============================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 数据库配置
DB_NAME="nfc_wallet"
DB_USER="root"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}NFC Campus Wallet - Database Reset${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# 警告提示
echo -e "${RED}⚠️  WARNING: This will DELETE ALL DATA in the database!${NC}"
echo -e "${RED}⚠️  警告：这将删除数据库中的所有数据！${NC}"
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${YELLOW}Operation cancelled.${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}Step 1: Creating backup...${NC}"
BACKUP_FILE="backups/backup_$(date +%Y%m%d_%H%M%S).sql"
mkdir -p backups

if mysqldump -u $DB_USER -p $DB_NAME > $BACKUP_FILE 2>/dev/null; then
    echo -e "${GREEN}✓ Backup created: $BACKUP_FILE${NC}"
else
    echo -e "${YELLOW}⚠ Backup failed or skipped (database might be empty)${NC}"
fi

echo ""
echo -e "${YELLOW}Step 2: Dropping all tables, views, and procedures...${NC}"
mysql -u $DB_USER -p $DB_NAME < migrations/drop_all_tables.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ All tables dropped successfully${NC}"
else
    echo -e "${RED}✗ Failed to drop tables${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 3: Reinitializing database...${NC}"
mysql -u $DB_USER -p $DB_NAME < migrations/complete_database_init.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Database reinitialized successfully${NC}"
else
    echo -e "${RED}✗ Failed to reinitialize database${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Database reset completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Default admin account:${NC}"
echo -e "  Username: ${GREEN}admin${NC}"
echo -e "  Password: ${GREEN}admin123${NC}"
echo ""
echo -e "${RED}⚠️  Please change the default password immediately!${NC}"
echo ""

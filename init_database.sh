#!/bin/bash

# ============================================================================
# NFC Campus Wallet - Database Initialization Script
# 数据库初始化脚本
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

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}NFC Campus Wallet - Database Initialization${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查 MySQL 是否安装
if ! command -v mysql &> /dev/null; then
    echo -e "${RED}Error: MySQL is not installed!${NC}"
    exit 1
fi

# 提示输入密码
echo -e "${YELLOW}Please enter MySQL root password:${NC}"
read -s DB_PASSWORD
echo ""

# 测试数据库连接
echo -e "${YELLOW}Testing database connection...${NC}"
if ! mysql -u"$DB_USER" -p"$DB_PASSWORD" -e "SELECT 1;" &> /dev/null; then
    echo -e "${RED}Error: Cannot connect to MySQL!${NC}"
    echo -e "${RED}Please check your username and password.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Database connection successful${NC}"
echo ""

# 询问是否要删除现有数据库
echo -e "${YELLOW}Do you want to DROP the existing database and recreate it?${NC}"
echo -e "${YELLOW}WARNING: This will DELETE ALL DATA!${NC}"
echo -e "${YELLOW}Type 'yes' to confirm, or anything else to skip:${NC}"
read CONFIRM

if [ "$CONFIRM" = "yes" ]; then
    echo -e "${YELLOW}Dropping existing database...${NC}"
    mysql -u"$DB_USER" -p"$DB_PASSWORD" -e "DROP DATABASE IF EXISTS $DB_NAME;"
    echo -e "${GREEN}✓ Database dropped${NC}"
fi

# 创建数据库
echo -e "${YELLOW}Creating database...${NC}"
mysql -u"$DB_USER" -p"$DB_PASSWORD" -e "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
echo -e "${GREEN}✓ Database created: $DB_NAME${NC}"
echo ""

# 执行初始化脚本
echo -e "${YELLOW}Running initialization script...${NC}"
if [ -f "migrations/init_database_mysql.sql" ]; then
    mysql -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < migrations/init_database_mysql.sql
    echo -e "${GREEN}✓ Database initialized successfully${NC}"
else
    echo -e "${RED}Error: init_database_mysql.sql not found!${NC}"
    exit 1
fi
echo ""

# 显示统计信息
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Database Statistics:${NC}"
echo -e "${GREEN}========================================${NC}"
mysql -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "
SELECT 'Events' AS table_name, COUNT(*) AS count FROM events
UNION ALL
SELECT 'Participants', COUNT(*) FROM participants
UNION ALL
SELECT 'Accounts', COUNT(*) FROM accounts
UNION ALL
SELECT 'Booths', COUNT(*) FROM booths
UNION ALL
SELECT 'Products', COUNT(*) FROM products
UNION ALL
SELECT 'Users', COUNT(*) FROM users
UNION ALL
SELECT 'Transactions', COUNT(*) FROM transactions;
"
echo ""

# 显示管理员账户信息
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Default Admin Account:${NC}"
echo -e "${GREEN}========================================${NC}"
mysql -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "
SELECT id, username, role, status, created_at 
FROM users 
WHERE role = 'super_admin';
"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Initialization Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Default Admin Credentials:${NC}"
echo -e "  Username: ${GREEN}admin${NC}"
echo -e "  Password: ${GREEN}admin123${NC}"
echo ""
echo -e "${RED}⚠️  IMPORTANT: Please change the default password immediately!${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "  1. Update .env file with database credentials"
echo -e "  2. Restart the backend service: ${GREEN}sudo systemctl restart nfc-wallet${NC}"
echo -e "  3. Login to web admin and change password"
echo ""

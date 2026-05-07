#!/bin/bash

# ============================================================================
# Apply Migration 005 - Add Missing Columns
# 应用迁移 005 - 添加缺失的字段
# ============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

DB_NAME="nfc_wallet"
DB_USER="root"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Applying Migration 005${NC}"
echo -e "${GREEN}Add Missing Columns to Database${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 提示输入密码
echo -e "${YELLOW}Please enter MySQL root password:${NC}"
read -s DB_PASSWORD
echo ""

# 测试数据库连接
echo -e "${YELLOW}Testing database connection...${NC}"
if ! mysql -u"$DB_USER" -p"$DB_PASSWORD" -e "SELECT 1;" &> /dev/null; then
    echo -e "${RED}Error: Cannot connect to MySQL!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Connection successful${NC}"
echo ""

# 执行迁移
echo -e "${YELLOW}Applying migration...${NC}"
mysql -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < migrations/005_add_missing_columns.sql

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Migration 005 Applied Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Restart backend service: ${GREEN}sudo systemctl restart nfc-wallet${NC}"
echo -e "  2. Check service status: ${GREEN}sudo systemctl status nfc-wallet${NC}"
echo -e "  3. Test Android app login and booth selection"
echo ""

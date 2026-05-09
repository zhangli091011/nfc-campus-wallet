#!/bin/bash

# ============================================================================
# 应用密码修复脚本
# Apply Password Fix Script
# ============================================================================

set -e

echo "========================================"
echo "应用密码修复"
echo "========================================"
echo ""

# 加载环境变量
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "❌ 错误: .env 文件不存在"
    exit 1
fi

# 数据库连接信息
DB_HOST="${DATABASE_HOST:-localhost}"
DB_PORT="${DATABASE_PORT:-3306}"
DB_USER="${DATABASE_USER:-root}"
DB_PASSWORD="${DATABASE_PASSWORD}"
DB_NAME="${DATABASE_NAME:-nfc_wallet}"

echo "数据库连接信息:"
echo "  主机: $DB_HOST"
echo "  端口: $DB_PORT"
echo "  用户: $DB_USER"
echo "  数据库: $DB_NAME"
echo ""

# 执行密码修复
echo "正在应用密码修复..."
mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < fix_user_passwords.sql

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 密码修复成功！"
    echo ""
    echo "更新后的登录凭据:"
    echo "  管理员:"
    echo "    用户名: admin"
    echo "    密码: admin123"
    echo ""
    echo "  收银员 (booth1_cashier ~ booth5_cashier):"
    echo "    密码: cashier123"
    echo ""
    echo "  充值员 (issuer1):"
    echo "    密码: cashier123"
else
    echo ""
    echo "❌ 密码修复失败"
    exit 1
fi

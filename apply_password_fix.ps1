# ============================================================================
# 应用密码修复脚本 (PowerShell)
# Apply Password Fix Script
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "应用密码修复" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 读取 .env 文件
if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            Set-Variable -Name $name -Value $value -Scope Script
        }
    }
} else {
    Write-Host "❌ 错误: .env 文件不存在" -ForegroundColor Red
    exit 1
}

# 数据库连接信息
$DB_HOST = if ($DATABASE_HOST) { $DATABASE_HOST } else { "localhost" }
$DB_PORT = if ($DATABASE_PORT) { $DATABASE_PORT } else { "3306" }
$DB_USER = if ($DATABASE_USER) { $DATABASE_USER } else { "root" }
$DB_PASSWORD = $DATABASE_PASSWORD
$DB_NAME = if ($DATABASE_NAME) { $DATABASE_NAME } else { "nfc_wallet" }

Write-Host "数据库连接信息:"
Write-Host "  主机: $DB_HOST"
Write-Host "  端口: $DB_PORT"
Write-Host "  用户: $DB_USER"
Write-Host "  数据库: $DB_NAME"
Write-Host ""

# 使用 Python 脚本执行 SQL（因为 Windows 可能没有 mysql 命令）
Write-Host "正在应用密码修复..." -ForegroundColor Yellow

$pythonScript = @"
import sys
sys.path.insert(0, '.')

from sqlalchemy import create_engine, text
from core.config import load_settings, get_settings

# 加载配置
load_settings()
settings = get_settings()

# 创建数据库连接
engine = create_engine(settings.database_url)

# 读取 SQL 文件
with open('fix_user_passwords.sql', 'r', encoding='utf-8') as f:
    sql_content = f.read()

# 分割 SQL 语句
sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip() and not stmt.strip().startswith('--')]

# 执行 SQL 语句
with engine.connect() as conn:
    for stmt in sql_statements:
        if stmt.strip().upper().startswith('USE'):
            continue  # 跳过 USE 语句
        try:
            result = conn.execute(text(stmt))
            conn.commit()
            
            # 如果是 SELECT 语句，打印结果
            if stmt.strip().upper().startswith('SELECT'):
                rows = result.fetchall()
                if rows:
                    for row in rows:
                        print(row)
        except Exception as e:
            print(f'执行 SQL 出错: {e}')
            print(f'SQL: {stmt[:100]}...')

print('\n✅ 密码修复成功！')
"@

# 将 Python 脚本写入临时文件
$pythonScript | Out-File -FilePath "temp_fix_passwords.py" -Encoding UTF8

# 执行 Python 脚本
python temp_fix_passwords.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ 密码修复成功！" -ForegroundColor Green
    Write-Host ""
    Write-Host "更新后的登录凭据:" -ForegroundColor Cyan
    Write-Host "  管理员:"
    Write-Host "    用户名: admin"
    Write-Host "    密码: admin123"
    Write-Host ""
    Write-Host "  收银员 (booth1_cashier ~ booth5_cashier):"
    Write-Host "    密码: cashier123"
    Write-Host ""
    Write-Host "  充值员 (issuer1):"
    Write-Host "    密码: cashier123"
    
    # 删除临时文件
    Remove-Item "temp_fix_passwords.py" -ErrorAction SilentlyContinue
} else {
    Write-Host ""
    Write-Host "❌ 密码修复失败" -ForegroundColor Red
    Remove-Item "temp_fix_passwords.py" -ErrorAction SilentlyContinue
    exit 1
}

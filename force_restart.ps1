# 强制重启后端服务
Write-Host "🔄 强制重启NFC钱包后端服务..." -ForegroundColor Cyan
Write-Host "=" * 60

# 停止所有Python进程
Write-Host "`n📍 正在停止所有Python进程..." -ForegroundColor Yellow
$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue

if ($pythonProcesses) {
    $pythonProcesses | ForEach-Object {
        Write-Host "  停止进程 ID: $($_.Id)" -ForegroundColor Gray
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "✅ 所有Python进程已停止" -ForegroundColor Green
} else {
    Write-Host "ℹ️  没有发现运行中的Python进程" -ForegroundColor Gray
}

# 等待进程完全停止
Write-Host "`n⏳ 等待进程完全停止..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

# 确认端口已释放
Write-Host "`n🔍 检查8000端口..." -ForegroundColor Yellow
$port8000 = netstat -ano | Select-String ":8000.*LISTENING"
if ($port8000) {
    Write-Host "⚠️  端口8000仍被占用，尝试强制释放..." -ForegroundColor Yellow
    $port8000 | ForEach-Object {
        $line = $_.Line
        if ($line -match "\s+(\d+)\s*$") {
            $pid = $matches[1]
            Write-Host "  停止进程 PID: $pid" -ForegroundColor Gray
            taskkill /F /PID $pid 2>$null
        }
    }
    Start-Sleep -Seconds 1
}

# 启动服务
Write-Host "`n🚀 正在启动服务..." -ForegroundColor Cyan
Start-Process python -ArgumentList "start_server.py" -NoNewWindow

# 等待服务启动
Write-Host "⏳ 等待服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# 检查服务是否启动成功
Write-Host "`n🔍 验证服务状态..." -ForegroundColor Yellow

$maxRetries = 5
$retryCount = 0
$serviceStarted = $false

while ($retryCount -lt $maxRetries -and -not $serviceStarted) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2
        if ($response.StatusCode -eq 200) {
            $serviceStarted = $true
            Write-Host "✅ 服务启动成功！" -ForegroundColor Green
        }
    } catch {
        $retryCount++
        if ($retryCount -lt $maxRetries) {
            Write-Host "  尝试 $retryCount/$maxRetries - 等待服务响应..." -ForegroundColor Gray
            Start-Sleep -Seconds 2
        }
    }
}

if (-not $serviceStarted) {
    Write-Host "❌ 服务启动失败或超时" -ForegroundColor Red
    Write-Host "请手动检查日志" -ForegroundColor Yellow
    exit 1
}

# 显示服务信息
Write-Host "`n📊 服务信息:" -ForegroundColor Cyan
Write-Host "   - 地址: http://localhost:8000" -ForegroundColor White
Write-Host "   - 健康检查: http://localhost:8000/health" -ForegroundColor White
Write-Host "   - API文档: http://localhost:8000/docs" -ForegroundColor White

# 运行CORS测试
Write-Host "`n🧪 运行CORS测试..." -ForegroundColor Cyan
Write-Host "=" * 60
python test_cors.py

Write-Host "`n" + "=" * 60
Write-Host "✅ 重启完成！" -ForegroundColor Green
Write-Host "`n💡 下一步:" -ForegroundColor Cyan
Write-Host "   1. 清除浏览器缓存 (Ctrl+Shift+Delete)" -ForegroundColor White
Write-Host "   2. 硬刷新前端页面 (Ctrl+Shift+R)" -ForegroundColor White
Write-Host "   3. 访问报表中心测试功能" -ForegroundColor White

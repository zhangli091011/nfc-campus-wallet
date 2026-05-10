# 重启后端服务器脚本

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "重启 NFC Campus Wallet 后端服务器" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 查找运行在8000端口的进程
Write-Host "🔍 查找运行在端口8000的进程..." -ForegroundColor Yellow
$port = 8000
$connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue

if ($connections) {
    foreach ($conn in $connections) {
        $processId = $conn.OwningProcess
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        
        if ($process) {
            Write-Host "📍 找到进程: $($process.ProcessName) (PID: $processId)" -ForegroundColor Green
            Write-Host "⏹️  停止进程..." -ForegroundColor Yellow
            Stop-Process -Id $processId -Force
            Write-Host "✅ 进程已停止" -ForegroundColor Green
        }
    }
    
    # 等待端口释放
    Write-Host "⏳ 等待端口释放..." -ForegroundColor Yellow
    Start-Sleep -Seconds 2
} else {
    Write-Host "ℹ️  端口8000未被占用" -ForegroundColor Gray
}

Write-Host ""
Write-Host "🚀 启动新的服务器实例..." -ForegroundColor Yellow
Write-Host ""

# 启动服务器
& python start_server.py

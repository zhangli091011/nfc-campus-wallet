@echo off
echo ============================================================
echo 重启 NFC Campus Wallet 后端服务器
echo ============================================================
echo.

echo 正在查找并停止运行在端口8000的进程...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo 找到进程 PID: %%a
    taskkill /F /PID %%a
)

echo.
echo 等待2秒...
timeout /t 2 /nobreak >nul

echo.
echo 启动新的服务器实例...
echo.
python start_server.py
